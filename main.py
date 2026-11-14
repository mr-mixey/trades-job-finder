from bakery import assert_equal
from dataclasses import dataclass
from drafter import *


@dataclass
class Job:
    """ one entry-level job from jobs.txt """
    title: str
    description: str
    mean_salary: float
    needs_id: bool
    needs_phone: bool
    training_required: bool


@dataclass
class State:
    """ everything the site remembers between pages """
    has_id: bool
    has_phone: bool
    ready_now: bool
    zip_code: str
    matches: list[Job]
    selected_job: str


def load_jobs() -> list[Job]:
    """ reads jobs.txt and returns a list of Job objects,
    one for each line in the file """
    job_list = []
    filename = "jobs.txt"
    jobs_file = open(filename)
    for line in jobs_file:
        clean_line = line.strip()
        parts = clean_line.split("|")
        job = Job(parts[0],
                  parts[1],
                  float(parts[2]),
                  parts[3] == "yes",
                  parts[4] == "yes",
                  parts[5] == "yes")
        job_list.append(job)
    jobs_file.close()
    return job_list


def find_matches(has_id: bool, has_phone: bool, ready_now: bool,
                 jobs: list[Job]) -> list[Job]:
    """ returns the jobs the user can start with what they have:
    an ID if the job needs one, a phone if the job needs one, and
    no required training if they need to start right away """
    matches = []
    for job in jobs:
        id_ok = has_id or not job.needs_id
        phone_ok = has_phone or not job.needs_phone
        training_ok = not ready_now or not job.training_required
        if id_ok and phone_ok and training_ok:
            matches.append(job)
    return matches


def job_titles(jobs: list[Job]) -> list[str]:
    """ returns just the title of each job, in the same order """
    titles = []
    for job in jobs:
        titles.append(job.title)
    return titles


def format_pay(salary: float) -> str:
    """ turns 44000.0 into the text $44,000 """
    # ADVANCED TECHNIQUE (not from the course): the built-in format function
    # turns a number into text using a "format code". The code "," tells it to
    # put a comma between each group of three digits, so format(44000, ",")
    # gives "44,000". int(salary) first drops the ".0" so we get "44,000"
    # instead of "44,000.0". Then we add the "$" on the front ourselves.
    return "$" + format(int(salary), ",")


def yes_no(value: bool) -> str:
    """ turns True into Yes and False into No """
    if value:
        return "Yes"
    return "No"


def describe_job(title: str, jobs: list[Job]) -> str:
    """ returns a few lines of text about the job with the given title,
    or a short message if no job has that title """
    found = "Sorry, that job could not be found."
    for job in jobs:
        if job.title == title:
            found = (job.description + "\n\n" +
                     "Typical pay: " + format_pay(job.mean_salary) + " per year\n" +
                     "ID usually required: " + yes_no(job.needs_id) + "\n" +
                     "Phone usually required: " + yes_no(job.needs_phone) + "\n" +
                     "Training required first: " + yes_no(job.training_required) + "\n")
    return found


@route
def index(state: State) -> Page:
    """ home page: explains the site and links to the questions """
    return Page(state, [
        Header("Trades Job Finder", 1),
        "Answer a few quick questions and see entry-level jobs that may fit you right now.\n",
        "This site does not save any personal information.\n\n",
        Button("Start", questions),
        Button("About this site", about)])


@route
def questions(state: State) -> Page:
    """ quiz page: a short form whose answers go to results """
    return Page(state, [
        Header("A few quick questions", 2),
        "Check each box that is true for you.\n\n",
        CheckBox("has_id", state.has_id),
        " I have a government ID\n",
        CheckBox("has_phone", state.has_phone),
        " I have a working phone number\n",
        CheckBox("ready_now", state.ready_now),
        " I need to start work as soon as possible\n\n",
        "Zip code (optional): ",
        TextBox("zip_code", state.zip_code),
        "\n\n",
        Button("See my matches", results),
        Button("Back", index)])


@route
def results(state: State, has_id: bool, has_phone: bool,
            ready_now: bool, zip_code: str) -> Page:
    """ saves the quiz answers, finds the matching jobs,
    and shows them """
    state.has_id = has_id
    state.has_phone = has_phone
    state.ready_now = ready_now
    state.zip_code = zip_code
    all_jobs = load_jobs()
    state.matches = find_matches(has_id, has_phone, ready_now, all_jobs)
    return show_matches(state)


@route
def show_matches(state: State) -> Page:
    """ lists the saved matches, or goes to no_matches if there are none """
    if state.matches == []:
        return no_matches(state)
    content = [Header("Jobs that may fit you", 2),
               str(len(state.matches)) + " jobs found.\n\n"]
    for job in state.matches:
        content.append("- " + job.title + " (" +
                       format_pay(job.mean_salary) + " per year)\n")
    content.append("\nPick a job to learn more:\n")
    content.append(SelectBox("job_title", job_titles(state.matches),
                             state.matches[0].title))
    content.append(Button("View details", job_detail))
    content.append(Button("Change my answers", questions))
    return Page(state, content)


@route
def job_detail(state: State, job_title: str) -> Page:
    """ shows pay, requirements, and training for the chosen job """
    state.selected_job = job_title
    return Page(state, [
        Header(job_title, 2),
        describe_job(job_title, load_jobs()),
        "\n",
        Button("Back to my matches", show_matches),
        Button("Find local help", resources),
        Button("Start over", index)])


@route
def no_matches(state: State) -> Page:
    """ shown when no job fits the answers, with ideas for what to try """
    return Page(state, [
        Header("No matches right now", 2),
        "No jobs fit those answers yet. That does not mean there is no path forward.\n\n",
        "Try changing your answers. For example, if you checked that you need to start ",
        "as soon as possible, unchecking it will include jobs that start with training.\n\n",
        "If you are missing an ID or phone, the local help page lists places that can help.\n\n",
        Button("Change my answers", questions),
        Button("Find local help", resources)])


@route
def resources(state: State) -> Page:
    """ points to free national services that can connect the user
    with local job and training help """
    if state.selected_job == "":
        heading = "Local help"
    else:
        heading = "Local help for: " + state.selected_job
    if state.zip_code == "":
        zip_line = "Enter your zip code in the locator below to find offices near you.\n\n"
    else:
        zip_line = "Use your zip code (" + state.zip_code + ") in the locator below.\n\n"
    return Page(state, [
        Header(heading, 2),
        zip_line,
        "American Job Center locator: careeronestop.org (search Service Locator)\n",
        "Free career help line: 1-877-872-5627\n",
        "Apprenticeship programs: apprenticeship.gov\n",
        "Housing and basic needs help: dial 211 or visit 211.org\n\n",
        "Hours and services change, so call ahead if you can.\n\n",
        Button("Back to my matches", show_matches),
        Button("Start over", index)])


@route
def about(state: State) -> Page:
    """ explains where the data comes from and how it should be used """
    return Page(state, [
        Header("About this site", 2),
        "This site matches the answers you give to a list of entry-level jobs. ",
        "The job list and pay figures are approximate and based on typical ",
        "national data (see O*NET at onetonline.org and the Bureau of Labor ",
        "Statistics at bls.gov). Employers vary, so treat results as ideas ",
        "to look into, not guarantees.\n\n",
        "Your answers are only used while you are on the site. Nothing is saved.\n\n",
        Button("Back", index)])


assert_equal(len(load_jobs()), 100)
assert_equal(load_jobs()[0].title, "Construction Laborer")
assert_equal(load_jobs()[2], Job("Flagger",
                              "Directs traffic around road and utility work zones using signs and signals.",
                              38000.0, True, True, True))
assert_equal(len(find_matches(False, False, False, load_jobs())), 14)
assert_equal(len(find_matches(True, True, False, load_jobs())), 100)
assert_equal(len(find_matches(True, True, True, load_jobs())), 73)
assert_equal(format_pay(44000.0), "$44,000")

set_website_title("Trades Job Finder")
set_site_information(
    author="Your Name",
    description="Find entry-level trades and labor jobs that fit what you have right now.",
    sources="Job and pay figures are approximate, based on O*NET (onetonline.org) and the Bureau of Labor Statistics (bls.gov). Thanks to the Drafter docs.",
    planning=["plan.pdf", "design.pdf"],
    links=["https://github.com/your-username/your-repository"]
)
hide_debug_information()
set_website_framed(False)

start_server(State(False, False, False, "", [], ""))
