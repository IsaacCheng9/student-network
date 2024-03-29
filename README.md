# Student Network - Reconnect

[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![CI](https://github.com/IsaacCheng9/student-network/actions/workflows/main.yml/badge.svg)

A student network which promotes interaction within the student community.
This aims to provide social opportunities by encouraging students to engage with
each other in a fun and friendly online environment.

## Screenshots

![Profile](https://user-images.githubusercontent.com/47993930/148656392-dd7c2eb8-f495-45d2-ba2b-33a0c6aba631.png)
![Member List](https://user-images.githubusercontent.com/47993930/148656401-5a0e245f-183e-4535-97d1-58018b8b0644.png)
![Connection Requests](https://user-images.githubusercontent.com/47993930/148656410-df269b00-2ef9-4622-b6fc-4588e5d6a3d5.png)
![Posting to Feed](https://user-images.githubusercontent.com/47993930/148656419-cff8cd16-abdb-46d2-9a81-cd65669ef67c.png)
![Achievements](https://user-images.githubusercontent.com/47993930/148656427-21b91681-ebea-4898-8710-34d164c26963.png)
![Leaderboard](https://user-images.githubusercontent.com/47993930/148656429-c92419ff-9a23-44aa-8e78-41f7dbf3b528.png)
![Taking Quizzes](https://user-images.githubusercontent.com/47993930/148656440-ebe6b74b-ccdd-4277-a258-5bd467155bb2.png)
![Quiz Results](https://user-images.githubusercontent.com/47993930/148656480-ae105aaa-26b9-4111-a168-ba383bcc0cbf.png)

## Installation

### Python Version

The application has been developed and tested to work on Python 3.8 and onwards.

### Running the Application Locally

To run the application, you should follow the following steps:

1. Clone this GitHub repository.
2. Ensure that you're in the root directory: `student-network`
3. Install the required Python libraries: `pip install -r requirements.txt`
4. Install the code as a package on your local machine with the command:
   `pip install -e .`
5. Run the application with the command: `python -m student_network.app`
6. Navigate to http://127.0.0.1:5000/ in your web browser.

## Usage

Upon opening the application, you will be greeted with a home page. From here,
you can log into your existing account, or you can register a new account. It
should be noted that registration will only work with university email
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
it easier to demo the product. The users `barn354` and `ic324`, both with
password `Password01`, have been set up with a full student profile and multiple
posts.

The following dummy accounts have been set up:

- `student1`, `student2`, `student3`, and `student4` for student accounts.
- `staffuser` and `staffusertwo` for staff accounts.
- `adminuser` for an administrator account.

## Documentation

### Requirements Analysis

Requirements analysis has been encapsulated through our research documents on
potential solutions, design thinking plan, and MoSCoW matrix. They can be found
in the following path: [docs/requirements-analysis](docs/requirements-analysis)

### Poster

A promotional poster has been designed for this project. It can be found in the
following GitHub repository
path: [docs/designs/poster.pdf](docs/designs/poster.pdf)
