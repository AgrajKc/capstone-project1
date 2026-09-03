from flask import Flask, redirect, render_template, request, session, url_for

from db import add_entry, delete_entry, get_all_entries, init_db, update_entry

app = Flask(__name__)

# Needed so Flask can remember in-progress answers between questions.
app.secret_key = "why-local-learning-key"

init_db()

QUESTIONS = [
    {
        "key": "problem",
        "prompt": "What went wrong?",
        "placeholder": "Don't make it sound perfect. Just tell me what happened.",
    },
    {
        "key": "why_it_happened",
        "prompt": "Why do you think it happened?",
        "placeholder": "What's the first reason that comes to mind?",
    },
    {
        "key": "deeper_why",
        "prompt": "And why did that happen?",
        "placeholder": "Don't stop at the first answer. Go one layer deeper.",
    },
    {
        "key": "next_time",
        "prompt": "What would you do differently next time?",
        "placeholder": "It doesn't have to be a big change. Start small.",
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
    entries = get_all_entries()
    return render_template("index.html", reflection_count=len(entries))


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
            error = "Take your time. Write a little something before continuing."
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

                return redirect(url_for("reflection_complete"))

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


@app.route("/reflection-complete")
def reflection_complete():
    return render_template("complete.html")


@app.route("/entries")
def entries():
    return render_template("entries.html", entries=get_all_entries())


@app.route("/edit/<int:entry_id>", methods=["GET", "POST"])
def edit_entry(entry_id):
    entries = get_all_entries()
    entry = next((item for item in entries if item["id"] == entry_id), None)

    if entry is None:
        return redirect(url_for("entries"))

    error = None

    if request.method == "POST":
        problem = request.form.get("problem", "").strip()
        why_it_happened = request.form.get("why_it_happened", "").strip()
        deeper_why = request.form.get("deeper_why", "").strip()
        next_time = request.form.get("next_time", "").strip()

        if not problem or not why_it_happened or not deeper_why or not next_time:
            error = "Please fill in all four answers."
        else:
            update_entry(
                entry_id,
                problem,
                why_it_happened,
                deeper_why,
                next_time,
            )

            return redirect(url_for("entries"))

    return render_template(
        "edit.html",
        entry=entry,
        error=error,
    )


@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete_entry_route(entry_id):
    delete_entry(entry_id)
    return redirect(url_for("entries"))


if __name__ == "__main__":
    app.run(debug=True)
