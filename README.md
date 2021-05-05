# Student Network - Reconnect

A student network which promotes interaction within the University of Exeter's
student community. This aims to provide social opportunities by encouraging
students to engage with each other in a fun and friendly online environment.

## Screenshots

![Profile](https://i.imgur.com/gvVlsvb.png)
![Member List](https://i.imgur.com/7m3OdIb.png?1)
![Connection Requests](https://i.imgur.com/mjyQ0it.png?1)
![Posting to Feed](https://i.imgur.com/Dh43VH6.png?1)
![Achievements](https://i.imgur.com/9wpoogO.png?1)
![Leaderboard](https://i.imgur.com/tpaaVpK.png?1)
![Taking Quizzes](https://i.imgur.com/mxKdQbC.png?1)
![Quiz Results](https://i.imgur.com/1ox2mcu.png?1)

## Contributors

- Isaac Cheng
- Ryan Storey
- Sofia Reid
- Barnie Gill
- Oskar Oramus
- Sam Shailer

## Installation

### Python Version

The application has been developed and tested to work on Python 3.8 and onwards.

### Python Libraries

This project uses several Python libraries. To run the application locally, you
should `pip install` the following:

- click
- email-validator
- Flask
- itsdangerous
- Jinja2
- MarkupSafe
- passlib
- Werkzeug
- Pillow

For example, you should `pip install passlib`.

### Virtual Environment

Alternatively, a virtual environment has been included in the GitHub repository.
This includes all the Python libraries required to run the application locally.

### Running the Application

To run the application, you should follow the following steps:

1. Clone this GitHub repository.
2. Navigate to the following directory in your terminal:
   [src](src).
3. Ensure that you have the prerequisites to run the application (as explained
   in the previous section).
4. Run the application with the command `python application.py`.
5. Navigate to http://127.0.0.1:5000/ in your web browser.

## Usage

Upon opening the application, you will be greeted with a home page. From here,
you can log into your existing account, or you can register a new account. It
should be noted that registration will only work with University of Exeter email
addresses, and academics will be sent for manual verification after signing up.

When you log in, you will be redirected to your profile page. This displays
information about you, such as your hobbies, interests, your rarest achievements
unlocked, and links to your social media profiles. Posts made by you are also
displayed on this page.

By default, some details will be filled in for you, such as your profile
picture, bio, date of birth, and gender. You can edit all these details by
pressing the 'Edit Profile' button.

To search for other members on the Reconnect network, you can navigate to the
'Members' page using the navigation bar on the top. From here, you can search by
the username, with the option of searching by a common hobby and/or interest
too. Search results will be displayed live with their username and their degree,
enabling you to visit the profiles of people and make connections.

Connections may be formed with people, with the option of marking connections as
close friends. Whereas connections must be accepted by people, you are able to
mark people as close friends without making a request. This also means that a
user may be your close friend, but you may not be their close friend; the close
friend system is one-way. If you wish to limit interaction with another user,
then you can block them. All these options may be accessed by navigating to a
user's profile.

You can view a list of your connections and pending connection requests on the
Connections page. Users who you have marked as a close friend have an icon of a
handshake next to them.

On your feed, you can view all the posts of people who you have connected with.
This is sorted in chronological order, with the newest posts appearing at the
top. You can also make new posts from this page; these are categorised as a text
post, an image post, or a link post.

Achievements may be unlocked by performing tasks on the Reconnect network. You
can view these on the Achievements page, which displays your progress with
achievements as a percentage, and the achievements you have completed, starting
from the most recent. This page also shows you which achievements you are yet to
unlock. Hovering over each achievement shows the title of the achievement,
description, and number of XP gained by unlocking it. Each of these achievements
has its own unique icon. Watch out for hidden achievements which are not
displayed until you unlock them; these will reward you with extra XP!

You will level up your profile based on how much XP you have gained. This
encourages some healthy competition in the Reconnect network. By interacting
more in various parts of the application, you will quickly be able to climb up
the leaderboard!

We have also provided you with an easy way to test and share your knowledge on
the Quizzes page. From here, you can create a quiz consisting of five
multiple-choice questions for others to complete. You can also view and take
part in quizzes made from other people.

## Demo Instructions

For testing purposes, we have created a lot of accounts and sample data to make
it easier to demo the product. This includes the users `barn354` and `ic324`,
both with password `Password01`, have been set up with a full student profile
and multiple posts.

The following dummy accounts have been set up:

- `student1`, `student2`, `student3`, and `student4` for student accounts.
- `staffuser` and `staffusertwo` for staff accounts.
- `adminuser` for an administrator account.

## Poster

A promotional poster has been designed for this project. It can be found in the
following GitHub repository
path: [docs/designs/poster.pdf](docs/designs/poster.pdf)

## Tests

All tests have been documented formally in a `.docx` file, which can be found at
the
following: [docs/test-log/Test Documentation.docx](docs/test-log/Test Documentation.docx)

### Unit Tests

We have performed unit testing through the `pytest` library in Python. These
have largely been focused towards auxiliary functions, as these are reused
repeatedly in the Python application.

### Integration Tests

Integration tests have been performed to ensure that different components of our
application work together in the system.

### User Acceptance Tests

We have evaluated the success criteria which we created before starting
development of this project, and how our product aligns with this. This has
ensured that our product meets the requirements of our stakeholders.

## GitHub Repository

The documentation and source files for our project can be found in our GitHub
repository as follows:

[https://github.com/IsaacCheng9/student-network](https://github.com/IsaacCheng9/student-network)

### Documentation

#### Kanban Methodology

Project management is handled using the Kanban methodology through a Trello
board, which can be found below:

[https://trello.com/b/xnKnkaxg/gsep-group-n](https://trello.com/b/xnKnkaxg/gsep-group-n)

We have taken regular snapshots of the Kanban board in Trello to archive our
progress. These can be found in the following path of the
repository: [docs/kanban-snapshots](docs/kanban-snapshots)

#### Meeting Minutes

In addition, minutes have been recorded for every group meeting. They can be
found in the following path: [docs/meeting-notes](docs/meeting-notes)

#### Requirements Analysis

Requirements analysis has been encapsulated through our research documents on
potential solutions, design thinking plan, and MoSCoW matrix. They can be found
in the following path: [docs/requirements-analysis](docs/requirements-analysis)