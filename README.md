# Large-Scale-Facial-Recognition

> A million scale facial recognition system.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Facial Recognition Software system to store and index millions of face-fingerprints and search for matches.

## Installation

Must have an NVIDIA gpu and cuda libraries installed for face recognition to work

OS X & Linux:

```sh
pip3 install -r requirements.txt
```

Windows:

```sh
pip install -r requirements.txt
```

## Usage example

First, you can setup the database configuration files (or just keep the default configuration) in _LSFR/core/FaceData/dbconfig.py_ and _LSFR/core/LSH/dbconfig.py_

Below example shows how to scrape an instagram profile to download all the images, store the face encodings and index them for easier search

```Python
from core.main import set_credentials, initialize, add

# set your instagram credentials to scrape instagram profiles
set_credentials("instagram", "your-instagram-username", "your-instagram-password")

# This is where you will store some important parameters and hash tables. NEVER LOSE THIS FOLDER
index = initialize("some/folder/my_epic_index")

# urls of profiles that you want to scrape
urls = [
    "https://www.instagram.com/veritasium/?hl=en",
    "https://www.instagram.com/thephysicsgirl/?hl=en",
]

# the add function will download every single image from the url and stores the face embeddings. If you run the add function on the same url again, then it will pickup where it left off (scrape any new images that were added after a while)
for url in urls:
    add(index, url)
```

Now lets look at how to find matching faces

```Python
from core.mappers import default_sql_mapper
from core.main import initialize, query, get_faces

index = initialize("some/folder/my_epic_index")

faces = []
for data in get_faces("some_image_that_has_a_face.jpg"):
    faces.append(data)

face_num, face_loc, face_embedding = faces[0]

# query function returns a list of matches where each match has information on the ID of face stored in database and the euclidean distance of the given face and the matched face (low distance = better match)
matches = query(index, default_sql_mapper, face_embedding, 20)

print(matches)

# you can use the IDs to query the FaceData database and get the link to the original post
```

## Meta

M. Zahash – zahash.z@gmail.com

Distributed under the MIT license. See `LICENSE` for more information.

[https://github.com/zahash/](https://github.com/zahash/)

## Contributing

1. Fork it (<https://github.com/zahash/LSFR/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request
