"""
Meeting Assistant Services
- TranscriptionService: Local speech-to-text with faster-whisper
- NotesGeneratorService: AI notes generation with Ollama
- ChatbotService: RAG-based Q&A with ChromaDB + Ollama
"""

import io
import json
import os
import tempfile
import threading
import logging

logger = logging.getLogger(__name__)

# ==================== TRANSCRIPTION SERVICE ====================

class TranscriptionService:
    """Local speech-to-text using faster-whisper."""

    def __init__(self, model_size="base"):
        self._model = None
        self._model_size = model_size
        self._lock = threading.Lock()

    def _get_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from faster_whisper import WhisperModel
                        self._model = WhisperModel(
                            self._model_size,
                            device="cpu",
                            compute_type="int8"
                        )
                        logger.info(f"Loaded faster-whisper model: {self._model_size}")
                    except Exception as e:
                        logger.error(f"Failed to load whisper model: {e}")
                        raise
        return self._model

    def transcribe_audio(self, audio_bytes):
        """Transcribe audio bytes (WAV format) and return list of segments."""
        model = self._get_model()

        # Write audio to temp file (faster-whisper needs a file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        try:
            segments, info = model.transcribe(
                temp_path,
                beam_size=5,
                language="en",
                vad_filter=True  # Filter out silence
            )

            results = []
            for segment in segments:
                results.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text.strip()
                })

            return results
        finally:
            os.unlink(temp_path)

    def is_available(self):
        """Check if whisper can be loaded."""
        try:
            self._get_model()
            return True
        except Exception:
            return False


# ==================== NOTES GENERATOR SERVICE ====================

class NotesGeneratorService:
    """Generate structured meeting notes using Ollama (local LLM)."""

    def __init__(self, model="llama3.2"):
        self._model = model

    def generate_notes(self, transcript_text, meeting_type="work"):
        """Generate structured notes from a full transcript.

        Args:
            transcript_text: The full meeting transcript as a string
            meeting_type: 'school' or 'work' - changes the prompt focus

        Returns:
            dict with keys: summary, topics, action_items, upcoming_tasks, key_decisions
        """
        try:
            import ollama
        except ImportError:
            logger.error("ollama package not installed")
            return self._empty_notes()

        if meeting_type == "school":
            prompt = self._school_prompt(transcript_text)
        else:
            prompt = self._work_prompt(transcript_text)

        try:
            response = ollama.chat(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                format="json"
            )

            content = response["message"]["content"]
            notes = json.loads(content)

            # Ensure all expected keys exist
            return {
                "summary": notes.get("summary", ""),
                "topics": notes.get("topics", []),
                "action_items": notes.get("action_items", []),
                "upcoming_tasks": notes.get("upcoming_tasks", []),
                "key_decisions": notes.get("key_decisions", [])
            }
        except Exception as e:
            logger.error(f"Notes generation failed: {e}")
            return self._empty_notes()

    def _school_prompt(self, transcript):
        return f"""Analyze this class/lecture transcript and extract structured notes.
Return a JSON object with these exact keys:

- "summary": A 2-3 sentence overview of what the class covered
- "topics": An array of topic strings discussed in the class
- "action_items": An array of homework, assignments, or things students need to do
- "upcoming_tasks": An array of objects with "task" and "date" keys for upcoming exams, deadlines, due dates mentioned
- "key_decisions": An array of important announcements or key concepts to remember

Be thorough but concise. Focus on what a student would need to study and prepare.

Transcript:
{transcript}"""

    def _work_prompt(self, transcript):
        return f"""Analyze this meeting transcript and extract structured notes.
Return a JSON object with these exact keys:

- "summary": A 2-3 sentence overview of the meeting
- "topics": An array of topic strings discussed
- "action_items": An array of objects with "task" and "owner" keys for action items assigned
- "upcoming_tasks": An array of objects with "task" and "date" keys for upcoming deadlines mentioned
- "key_decisions": An array of important decisions made during the meeting

Be thorough but concise. Focus on actionable information.

Transcript:
{transcript}"""

    def _empty_notes(self):
        return {
            "summary": "",
            "topics": [],
            "action_items": [],
            "upcoming_tasks": [],
            "key_decisions": []
        }

    def is_available(self):
        """Check if Ollama is running and the model is available."""
        try:
            import ollama
            ollama.list()
            return True
        except Exception:
            return False


# ==================== CHATBOT SERVICE (RAG) ====================

class ChatbotService:
    """RAG-based chatbot using ChromaDB + sentence-transformers + Ollama."""

    def __init__(self, persist_dir="chroma_db", ollama_model="llama3.2"):
        self._persist_dir = persist_dir
        self._ollama_model = ollama_model
        self._collection = None
        self._embedder = None
        self._client = None

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded sentence-transformers model")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return self._embedder

    def _get_collection(self):
        if self._client is None:
            try:
                import chromadb
                self._client = chromadb.PersistentClient(path=self._persist_dir)
                logger.info(f"ChromaDB initialized at {self._persist_dir}")
            except Exception as e:
                logger.error(f"Failed to init ChromaDB: {e}")
                raise
        return self._client

    def index_meeting(self, meeting_id, transcript_segments):
        """Index a meeting's transcript chunks into ChromaDB for RAG retrieval.

        Args:
            meeting_id: The meeting ID
            transcript_segments: List of dicts with 'text' and 'timestamp_sec'
        """
        client = self._get_collection()
        embedder = self._get_embedder()

        collection_name = f"meeting_{meeting_id}"
        # Delete existing collection if re-indexing
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

        collection = client.get_or_create_collection(name=collection_name)

        # Chunk transcripts into ~200 word pieces for better retrieval
        chunks = self._chunk_transcripts(transcript_segments)
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        embeddings = embedder.encode(texts).tolist()
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"meeting_id": str(meeting_id), "timestamp_sec": c.get("timestamp_sec", 0)} for c in chunks]

        collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

        # Also add to global collection for cross-meeting search
        global_collection = client.get_or_create_collection(name="all_meetings")
        global_ids = [f"m{meeting_id}_chunk_{i}" for i in range(len(chunks))]
        global_metadatas = [{"meeting_id": str(meeting_id), "timestamp_sec": c.get("timestamp_sec", 0)} for c in chunks]

        global_collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=global_ids,
            metadatas=global_metadatas
        )

        logger.info(f"Indexed {len(chunks)} chunks for meeting {meeting_id}")

    def ask(self, question, meeting_id=None):
        """Ask a question and get a RAG-powered answer.

        Args:
            question: The user's question
            meeting_id: If provided, search only this meeting. Otherwise search all meetings.

        Returns:
            dict with 'answer' and 'sources'
        """
        try:
            import ollama
        except ImportError:
            return {"answer": "Ollama is not installed. Please install it to use the chatbot.", "sources": []}

        client = self._get_collection()
        embedder = self._get_embedder()

        # Determine which collection to search
        if meeting_id:
            collection_name = f"meeting_{meeting_id}"
        else:
            collection_name = "all_meetings"

        try:
            collection = client.get_collection(name=collection_name)
        except Exception:
            return {"answer": "No transcript data found to search. Make sure the meeting has been transcribed.", "sources": []}

        # Embed the question and find relevant chunks
        query_embedding = embedder.encode([question]).tolist()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=5
        )

        if not results["documents"] or not results["documents"][0]:
            return {"answer": "I couldn't find relevant information in the transcript.", "sources": []}

        # Build context from retrieved chunks
        context_chunks = results["documents"][0]
        context = "\n\n".join(context_chunks)

        prompt = f"""Based on the following meeting transcript excerpts, answer the question.
If the answer isn't in the excerpts, say so honestly.

Transcript excerpts:
{context}

Question: {question}

Answer:"""

        try:
            response = ollama.chat(
                model=self._ollama_model,
                messages=[{"role": "user", "content": prompt}]
            )

            answer = response["message"]["content"]
            sources = []
            if results["metadatas"] and results["metadatas"][0]:
                for meta in results["metadatas"][0]:
                    sources.append({
                        "meeting_id": meta.get("meeting_id"),
                        "timestamp_sec": meta.get("timestamp_sec", 0)
                    })

            return {"answer": answer, "sources": sources}
        except Exception as e:
            logger.error(f"Chatbot query failed: {e}")
            return {"answer": f"Failed to generate answer: {str(e)}", "sources": []}

    def _chunk_transcripts(self, segments, max_words=200):
        """Combine transcript segments into chunks of ~max_words."""
        chunks = []
        current_text = ""
        current_timestamp = 0

        for seg in segments:
            text = seg.get("text", "")
            if not text:
                continue

            if not current_text:
                current_timestamp = seg.get("timestamp_sec", 0)

            current_text += " " + text

            if len(current_text.split()) >= max_words:
                chunks.append({
                    "text": current_text.strip(),
                    "timestamp_sec": current_timestamp
                })
                current_text = ""

        # Don't forget the last chunk
        if current_text.strip():
            chunks.append({
                "text": current_text.strip(),
                "timestamp_sec": current_timestamp
            })

        return chunks

    def delete_meeting_index(self, meeting_id):
        """Remove a meeting's data from ChromaDB."""
        client = self._get_collection()
        try:
            client.delete_collection(f"meeting_{meeting_id}")
        except Exception:
            pass
        # Also remove from global collection
        try:
            global_collection = client.get_collection("all_meetings")
            # Get all IDs that belong to this meeting
            results = global_collection.get(
                where={"meeting_id": str(meeting_id)}
            )
            if results["ids"]:
                global_collection.delete(ids=results["ids"])
        except Exception:
            pass
