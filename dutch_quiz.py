import streamlit as st
import pandas as pd
import random
 
# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dutch Quiz", page_icon="🇳🇱", layout="centered")
 
# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Cards */
.word-card {
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    margin: 1.5rem 0;
}
.word-card .dutch-word {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1a1a1a;
    margin: 0;
}
.word-card .meta {
    font-size: 0.8rem;
    color: #888;
    margin-top: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}
 
/* Score bar */
.score-bar {
    background: #f0f0f0;
    border-radius: 8px;
    padding: 0.75rem 1.25rem;
    display: flex;
    justify-content: space-between;
    margin-bottom: 1rem;
    font-size: 0.95rem;
    color: #444;
}
 
/* Feedback */
.feedback-correct {
    background: #edfaf3;
    border: 1px solid #a3d9b8;
    border-radius: 8px;
    padding: 0.75rem 1.25rem;
    color: #2e7d52;
    text-align: center;
    margin: 0.5rem 0;
}
.feedback-wrong {
    background: #fdf0f0;
    border: 1px solid #f0b8b8;
    border-radius: 8px;
    padding: 0.75rem 1.25rem;
    color: #c0392b;
    text-align: center;
    margin: 0.5rem 0;
}
 
/* Badge */
.badge {
    display: inline-block;
    background: #e8e8e8;
    color: #333;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)
 
# ── Load data ─────────────────────────────────────────────────────────────────
CSV_FILE = "dutch_words.csv"
 
@st.cache_data
def load_words(path):
    try:
        import chardet
        with open(path, "rb") as f:
            detected = chardet.detect(f.read())
        encoding = detected.get("encoding") or "latin-1"
    except ImportError:
        encoding = "latin-1"
    return pd.read_csv(path, encoding=encoding)
 
try:
    df = load_words(CSV_FILE)
except FileNotFoundError:
    st.error(f"Could not find `{CSV_FILE}`. Make sure it's in the same folder as this script.")
    st.stop()
 
# ── Session state init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "mode": None,           # selected game mode
        "score": 0,
        "total": 0,
        "question": None,       # current question dict
        "answered": False,
        "chosen": None,
        "wrong_answers": [],    # list of dicts for summary
        "finished": False,
        "filter_category": "All",
        "filter_difficulty": "All",
        "questions_per_session": 10,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
 
init_state()
 
# ── Helpers ───────────────────────────────────────────────────────────────────
def speak_button(word):
    """Render a small speaker button that pronounces the word using the browser's Web Speech API."""
    import streamlit.components.v1 as components
    safe_word = word.replace("'", "\\'")
    components.html(f"""
        <button onclick="
            var u = new SpeechSynthesisUtterance('{safe_word}');
            u.lang = 'nl-NL';
            u.rate = 0.9;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
        " style="
            background: none;
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 1.1rem;
            cursor: pointer;
            color: #444;
            margin-top: 0.5rem;
        ">🔊 Listen</button>
    """, height=50)
 
def get_filtered_df():
    d = df.copy()
    if st.session_state.filter_category != "All":
        d = d[d["category"] == st.session_state.filter_category]
    if st.session_state.filter_difficulty != "All":
        d = d[d["difficulty"] == st.session_state.filter_difficulty]
    return d
 
def new_question(mode, filtered):
    row = filtered.sample(1).iloc[0]
    if mode in ("multiple_choice", "speed"):
        wrong_pool = filtered[filtered["dutch"] != row["dutch"]]
        wrong_options = wrong_pool["english"].sample(min(4, len(wrong_pool))).tolist()
        options = wrong_options + [row["english"]]
        random.shuffle(options)
        return {
            "dutch": row["dutch"],
            "english": row["english"],
            "category": row["category"],
            "difficulty": row["difficulty"],
            "options": options,
        }
    elif mode == "reverse":
        wrong_pool = filtered[filtered["english"] != row["english"]]
        wrong_options = wrong_pool["dutch"].sample(min(4, len(wrong_pool))).tolist()
        options = wrong_options + [row["dutch"]]
        random.shuffle(options)
        return {
            "dutch": row["dutch"],
            "english": row["english"],
            "category": row["category"],
            "difficulty": row["difficulty"],
            "options": options,
            "reverse": True,
        }
    elif mode == "type_answer":
        return {
            "dutch": row["dutch"],
            "english": row["english"],
            "category": row["category"],
            "difficulty": row["difficulty"],
        }
    elif mode == "flashcard":
        return {
            "dutch": row["dutch"],
            "english": row["english"],
            "category": row["category"],
            "difficulty": row["difficulty"],
            "flipped": False,
        }
 
def reset_session():
    for k in ["score","total","question","answered","chosen","wrong_answers","finished","mode"]:
        if k in st.session_state:
            del st.session_state[k]
    init_state()
 
# ── HOME ──────────────────────────────────────────────────────────────────────
if st.session_state.mode is None and not st.session_state.finished:
 
    st.markdown("<h1 style='margin-bottom:0'>Dutch Quiz 🇳🇱</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#888;margin-top:0.25rem'>Test your Dutch vocabulary</p>", unsafe_allow_html=True)
 
    st.markdown("---")
 
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        cats = ["All"] + sorted(df["category"].unique().tolist())
        st.session_state.filter_category = st.selectbox("Category", cats)
    with col2:
        diffs = ["All"] + sorted(df["difficulty"].unique().tolist())
        st.session_state.filter_difficulty = st.selectbox("Topic", diffs)
    with col3:
        st.session_state.questions_per_session = st.selectbox("Questions", [5, 10, 15, 20], index=1)
 
    filtered = get_filtered_df()
    st.caption(f"📚 {len(filtered)} words available with current filters")
 
    st.markdown("### Choose a game mode")
 
    modes = [
        ("multiple_choice", "🔤 Multiple Choice", "Dutch → pick the English meaning from 5 options"),
        ("reverse",         "🔁 Reverse Quiz",    "English → pick the Dutch word from 5 options"),
        ("type_answer",     "✏️ Type the Answer", "Dutch → type the English meaning (no hints!)"),
        ("flashcard",       "🃏 Flashcard",        "See the word, flip to reveal, self-rate"),
        ("speed",           "⚡ Speed Round",      "Answer as many as you can in 60 seconds"),
    ]
 
    for mode_id, title, desc in modes:
        with st.container():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{title}**  \n<span style='color:#888;font-size:0.9rem'>{desc}</span>", unsafe_allow_html=True)
            with c2:
                if st.button("Play", key=mode_id):
                    if len(filtered) < 5:
                        st.error("Not enough words for this filter. Need at least 5.")
                    else:
                        st.session_state.mode = mode_id
                        st.session_state.question = new_question(mode_id, filtered)
                        if mode_id == "speed":
                            import time
                            st.session_state.speed_start = time.time()
                        st.rerun()
            st.markdown("<hr style='border-color:#1e1e2e;margin:0.5rem 0'>", unsafe_allow_html=True)
 
# ── FINISHED ──────────────────────────────────────────────────────────────────
elif st.session_state.finished:
    score = st.session_state.score
    total = st.session_state.total
    pct = int((score / total) * 100) if total > 0 else 0
 
    st.markdown(f"<h1>Session Complete! 🎉</h1>", unsafe_allow_html=True)
 
    emoji = "🏆" if pct >= 80 else "💪" if pct >= 50 else "📖"
    st.markdown(f"""
    <div class='word-card'>
        <div style='font-size:3rem'>{emoji}</div>
        <div class='dutch-word'>{score} / {total}</div>
        <div class='meta'>{pct}% correct</div>
    </div>
    """, unsafe_allow_html=True)
 
    if st.session_state.wrong_answers:
        st.markdown("### Words to review")
        review_df = pd.DataFrame(st.session_state.wrong_answers)
        review_df.columns = ["Dutch", "Correct Answer", "Your Answer"]
        st.dataframe(review_df, use_container_width=True, hide_index=True)
    else:
        st.success("Perfect score! No words to review. 🌟")
 
    if st.button("🏠 Back to Home", use_container_width=True):
        reset_session()
        st.rerun()
 
# ── QUIZ MODES ────────────────────────────────────────────────────────────────
else:
    mode = st.session_state.mode
    q = st.session_state.question
    filtered = get_filtered_df()
 
    # Header
    col_a, col_b = st.columns([3, 1])
    with col_a:
        mode_labels = {
            "multiple_choice": "🔤 Multiple Choice",
            "reverse": "🔁 Reverse Quiz",
            "type_answer": "✏️ Type the Answer",
            "flashcard": "🃏 Flashcard",
            "speed": "⚡ Speed Round",
        }
        st.markdown(f"<span class='badge'>{mode_labels.get(mode,'')}</span>", unsafe_allow_html=True)
    with col_b:
        if st.button("🏠 Quit"):
            reset_session()
            st.rerun()
 
    # Score bar
    total = st.session_state.total
    n = st.session_state.questions_per_session
    if mode != "speed":
        st.markdown(f"""
        <div class='score-bar'>
            <span>Question {total + 1} / {n}</span>
            <span>✅ {st.session_state.score} correct</span>
        </div>
        """, unsafe_allow_html=True)
 
    # ── SPEED ROUND ───────────────────────────────────────────────────────────
    if mode == "speed":
        import time
        elapsed = time.time() - st.session_state.get("speed_start", time.time())
        remaining = max(0, 60 - int(elapsed))
 
        st.markdown(f"""
        <div class='score-bar'>
            <span>⏱ {remaining}s remaining</span>
            <span>✅ {st.session_state.score} correct</span>
        </div>
        """, unsafe_allow_html=True)
 
        if remaining == 0 and not st.session_state.answered:
            st.session_state.finished = True
            st.session_state.total = st.session_state.score + len(st.session_state.wrong_answers)
            st.rerun()
 
        st.markdown(f"""
        <div class='word-card'>
            <p class='dutch-word'>{q['dutch']}</p>
            <p class='meta'>{q['category']} · {q['difficulty']}</p>
        </div>
        """, unsafe_allow_html=True)
        speak_button(q["dutch"])
 
        if not st.session_state.answered:
            cols = st.columns(2)
            for i, opt in enumerate(q["options"]):
                with cols[i % 2]:
                    if st.button(opt, key=f"opt_{i}", use_container_width=True):
                        st.session_state.answered = True
                        st.session_state.chosen = opt
                        if opt == q["english"]:
                            st.session_state.score += 1
                        else:
                            st.session_state.wrong_answers.append({
                                "dutch": q["dutch"],
                                "correct": q["english"],
                                "given": opt,
                            })
                        # immediately move to next
                        st.session_state.answered = False
                        st.session_state.question = new_question(mode, filtered)
                        st.rerun()
        else:
            st.session_state.answered = False
            st.session_state.question = new_question(mode, filtered)
            st.rerun()
 
    # ── MULTIPLE CHOICE / REVERSE ─────────────────────────────────────────────
    elif mode in ("multiple_choice", "reverse"):
        is_reverse = mode == "reverse"
        prompt_word = q["english"] if is_reverse else q["dutch"]
        prompt_label = "English → Dutch" if is_reverse else "Dutch → English"
 
        st.markdown(f"""
        <div class='word-card'>
            <p class='meta'>{prompt_label} · {q['category']} · {q['difficulty']}</p>
            <p class='dutch-word'>{prompt_word}</p>
        </div>
        """, unsafe_allow_html=True)
        speak_button(q["dutch"])
 
        correct_answer = q["dutch"] if is_reverse else q["english"]
 
        if not st.session_state.answered:
            cols = st.columns(2)
            for i, opt in enumerate(q["options"]):
                with cols[i % 2]:
                    if st.button(opt, key=f"opt_{i}", use_container_width=True):
                        st.session_state.answered = True
                        st.session_state.chosen = opt
                        if opt == correct_answer:
                            st.session_state.score += 1
                        else:
                            st.session_state.wrong_answers.append({
                                "dutch": q["dutch"],
                                "correct": correct_answer,
                                "given": opt,
                            })
                        st.rerun()
        else:
            chosen = st.session_state.chosen
            if chosen == correct_answer:
                st.markdown("<div class='feedback-correct'>✅ Correct!</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='feedback-wrong'>❌ Wrong — correct answer: <strong>{correct_answer}</strong></div>", unsafe_allow_html=True)
 
            st.session_state.total += 1
            if st.session_state.total >= n:
                if st.button("📊 See Results", use_container_width=True):
                    st.session_state.finished = True
                    st.rerun()
            else:
                if st.button("Next →", use_container_width=True):
                    st.session_state.answered = False
                    st.session_state.chosen = None
                    st.session_state.question = new_question(mode, filtered)
                    st.rerun()
 
    # ── TYPE THE ANSWER ───────────────────────────────────────────────────────
    elif mode == "type_answer":
        st.markdown(f"""
        <div class='word-card'>
            <p class='meta'>Dutch → English · {q['category']} · {q['difficulty']}</p>
            <p class='dutch-word'>{q['dutch']}</p>
        </div>
        """, unsafe_allow_html=True)
        speak_button(q["dutch"])
 
        if not st.session_state.answered:
            user_input = st.text_input("Your answer:", key="type_input", placeholder="Type in English...")
            if st.button("Submit", use_container_width=True):
                if user_input.strip():
                    st.session_state.answered = True
                    st.session_state.chosen = user_input.strip().lower()
                    if st.session_state.chosen == q["english"].lower():
                        st.session_state.score += 1
                    else:
                        st.session_state.wrong_answers.append({
                            "dutch": q["dutch"],
                            "correct": q["english"],
                            "given": user_input.strip(),
                        })
                    st.rerun()
        else:
            if st.session_state.chosen == q["english"].lower():
                st.markdown("<div class='feedback-correct'>✅ Correct!</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='feedback-wrong'>❌ Wrong — correct answer: <strong>{q['english']}</strong></div>", unsafe_allow_html=True)
 
            st.session_state.total += 1
            if st.session_state.total >= n:
                if st.button("📊 See Results", use_container_width=True):
                    st.session_state.finished = True
                    st.rerun()
            else:
                if st.button("Next →", use_container_width=True):
                    st.session_state.answered = False
                    st.session_state.chosen = None
                    st.session_state.question = new_question(mode, filtered)
                    st.rerun()
 
    # ── FLASHCARD ─────────────────────────────────────────────────────────────
    elif mode == "flashcard":
        flipped = q.get("flipped", False)
 
        if not flipped:
            st.markdown(f"""
            <div class='word-card'>
                <p class='meta'>What does this mean? · {q['category']} · {q['difficulty']}</p>
                <p class='dutch-word'>{q['dutch']}</p>
            </div>
            """, unsafe_allow_html=True)
            speak_button(q["dutch"])
            if st.button("🔄 Flip card", use_container_width=True):
                st.session_state.question["flipped"] = True
                st.rerun()
        else:
            st.markdown(f"""
            <div class='word-card'>
                <p class='meta'>{q['dutch']} means:</p>
                <p class='dutch-word'>{q['english']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**Did you know it?**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, I knew it", use_container_width=True):
                    st.session_state.score += 1
                    st.session_state.total += 1
                    if st.session_state.total >= n:
                        st.session_state.finished = True
                    else:
                        st.session_state.question = new_question(mode, filtered)
                    st.rerun()
            with col2:
                if st.button("❌ No, I didn't", use_container_width=True):
                    st.session_state.wrong_answers.append({
                        "dutch": q["dutch"],
                        "correct": q["english"],
                        "given": "—",
                    })
                    st.session_state.total += 1
                    if st.session_state.total >= n:
                        st.session_state.finished = True
                    else:
                        st.session_state.question = new_question(mode, filtered)
                    st.rerun()
