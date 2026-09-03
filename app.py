from flask import Flask, redirect, render_template, request, session, url_for

from db import add_entry, delete_entry, get_all_entries, init_db, update_entry

app = Flask(__name__)

app.secret_key = "why-local-learning-key"

init_db()

QUESTIONS = [
    {
        "key": "problem",
        "prompt": "What went wrong?",
        "stage": "Start with the facts",
        "placeholder": "Start with what actually happened. Don't worry about making it sound perfect.",
    },
    {
        "key": "why_it_happened",
        "prompt": "Why do you think it happened?",
        "stage": "Find the cause",
        "placeholder": "You know what happened. Now look for the reason behind it.",
    },
    {
        "key": "deeper_why",
        "prompt": "And why did that happen?",
        "stage": "Go deeper",
        "placeholder": "Don't stop at the first answer. Go one layer deeper.",
    },
    {
        "key": "next_time",
        "prompt": "What would you do differently next time?",
        "stage": "Look forward",
        "placeholder": "Turn what you discovered into something useful. Start small.",
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
    search_query = request.args.get("q", "").strip()
    entries = get_all_entries()

    if search_query:
        search = search_query.lower()
        entries = [
            entry
            for entry in entries
            if search in entry["problem"].lower()
            or search in entry["why_it_happened"].lower()
            or search in entry["deeper_why"].lower()
            or search in entry["next_time"].lower()
        ]

    return render_template(
        "entries.html",
        entries=entries,
        search_query=search_query,
    )


@app.route("/view/<int:entry_id>")
def view_entry(entry_id):
    entries = get_all_entries()
    entry = next((item for item in entries if item["id"] == entry_id), None)

    if entry is None:
        return redirect(url_for("entries"))

    return render_template("view.html", entry=entry)


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