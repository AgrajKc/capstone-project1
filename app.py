from flask import Flask, redirect, render_template, request, session, url_for

from db import add_entry, get_all_entries, init_db

app = Flask(__name__)
# Needed so Flask can remember in-progress answers between questions.
app.secret_key = "why-local-learning-key"
init_db()

QUESTIONS = [
    {
        "key": "problem",
        "prompt": "What went wrong?",
        "placeholder": "Tell it like you would to a friend.",
    },
    {
        "key": "why_it_happened",
        "prompt": "Why do you think it happened?",
        "placeholder": "The first reason that comes to mind.",
    },
    {
        "key": "deeper_why",
        "prompt": "And why did that happen?",
        "placeholder": "Go one layer underneath that reason.",
    },
    {
        "key": "next_time",
        "prompt": "What would you do differently next time?",
        "placeholder": "One small change is enough.",
    },
]


def get_draft():
    return session.get("draft", {})


def first_unanswered_step(draft):
    for index, question in enumerate(QUESTIONS, start=1):
        if not draft.get(question["key"]):
            return index
    return len(QUESTIONS)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/debug")
def debug():
    return redirect(url_for("debug_step", step=1))


@app.route("/debug/<int:step>", methods=["GET", "POST"])
def debug_step(step):
    if step < 1 or step > len(QUESTIONS):
        return redirect(url_for("debug_step", step=1))

    draft = get_draft()
    earliest_open = first_unanswered_step(draft)
    if step > earliest_open:
        return redirect(url_for("debug_step", step=earliest_open))

    question = QUESTIONS[step - 1]
    error = None
    answer = draft.get(question["key"], "")

    if request.method == "POST":
        answer = request.form.get("answer", "").strip()
        going_back = request.form.get("direction") == "back" and step > 1

        if going_back:
            if answer:
                draft[question["key"]] = answer
                session["draft"] = draft
            return redirect(url_for("debug_step", step=step - 1))

        if not answer:
            error = "Write a little something before continuing."
        else:
            draft[question["key"]] = answer
            session["draft"] = draft
            if step == len(QUESTIONS):
                add_entry(
                    draft["problem"],
                    draft["why_it_happened"],
                    draft["deeper_why"],
                    draft["next_time"],
                )
                session.pop("draft", None)
                return redirect(url_for("entries"))
            return redirect(url_for("debug_step", step=step + 1))

    return render_template(
        "debug.html",
        step=step,
        total=len(QUESTIONS),
        question=question,
        answer=answer,
        error=error,
        is_last=step == len(QUESTIONS),
    )


@app.route("/entries")
def entries():
    return render_template("entries.html", entries=get_all_entries())


if __name__ == "__main__":
    app.run(debug=True)
