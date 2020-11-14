import os
import pathlib
import json
import numpy as np

from sqlalchemy import func, and_
from collections import defaultdict

from .base import Base, ENGINE
from .models import Index, HashTables
from .utils import SessionCM, commit_add_db_row
from .minmaxheap import MinKList
from .config import NUM_TABLES, HASH_SIZE, EMBEDDING_SIZE

Base.metadata.create_all(ENGINE)


class NonEmptyDirectory(Exception):
    pass


class ENCDIST:
    def __init__(self, l_id, dist):
        self.l_id = l_id
        self.dist = dist

    def __repr__(self):
        return "<l_id={}; dist={}>".format(self.l_id, self.dist)

    def __lt__(self, other):
        return self.dist < other.dist

    def __le__(self, other):
        return self.dist <= other.dist

    def __gt__(self, other):
        return self.dist > other.dist

    def __ge__(self, other):
        return self.dist >= other.dist

    def __eq__(self, other):
        return self.dist == other.dist


class DiskLSH:
    """
    Disk based Locality Sensitive Hashing using Random Projection with Multiple hash tables
    """

    def __init__(self, index_dir="./index"):
        self.index_dir = pathlib.Path(index_dir)
        self.hash_dir = self.index_dir / "hash_tables"
        self.bucket_dir = self.index_dir / "buckets"
        self.params_file = self.index_dir / "params.json"
        self.global_idx_file = self.index_dir / "global_idx.txt"

    def set_params(self, num_tables, hash_size, embedding_size):
        """
        This method will save the given params to a json file inside <index_dir>
        and also generate and save the hash tables inside <index_dir>/hash_tables

        Args:
            num_tables: number of hash tables (random projection)
            hash_size: number of bits (or) number of output dimensions; Eg: 128 length input vector will be converted to a 8 bit index
            embedding_size: the length of each embedding vector; Eg: 128
        """
        if os.path.isdir(self.index_dir) and os.listdir(self.index_dir):
            raise NonEmptyDirectory("The folder specified by index_dir must be empty")

        self._params = {}
        self._params["num_tables"] = num_tables
        self._params["hash_size"] = hash_size
        self._params["embedding_size"] = embedding_size

        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.hash_dir.mkdir(parents=True, exist_ok=True)
        self.bucket_dir.mkdir(parents=True, exist_ok=True)

        self._save_params()
        self._generate_hash_tables()

    def add(self, id, arr):
        """Index the given vector (or matrix) by calculating and storing the hash
        in one of the buckets

        If arr is a matrix then each row must correspond to an embedding vector
        """
        hashes = self.get_hash(arr)
        unqiue_hashes = set(hashes)

        for h in unqiue_hashes:
            h = str(h)

            euclidean_index = self.get_euclidean_index(arr)
            selected_bucket_hash_euclidean = self.bucket_dir / h / euclidean_index
            selected_bucket_hash_euclidean.mkdir(parents=True, exist_ok=True)

            with (selected_bucket_hash_euclidean / "idx.txt").open("a") as f:
                f.write(str(id))
                f.write("\n")

            with self.global_idx_file.open("a") as f:
                f.write(str(id))
                f.write("\n")

    def query(self, mapper, arr, k=10):
        """
        mapper is a function which takes id as input and gives the
        encoding vector as output
        """
        matches = MinKList(k)

        local_ids = self.get_local_ids(arr)
        print("Found {} potential matches".format(len(local_ids)))
        for id_num, l_id in enumerate(local_ids):
            encoding_vec = mapper(l_id)
            dist = self.euclidean(arr, encoding_vec)

            matches.insert(ENCDIST(l_id, dist))

            print(".", end="")
            if id_num % 100 == 0:
                print()

        return sorted(matches.get_items())

    def get_local_ids(self, arr):
        """returns the ids that are present in the same hash bucket
        for the given encoding vector
        """
        target_euc_idx = float(self.get_euclidean_index(arr).replace("d", "."))

        hashes = self.get_hash(arr)
        unique_hashes = set(hashes)

        ids = set()
        for h in unique_hashes:
            h = str(h)
            selected_hash = self.bucket_dir / h
            for euclidean_dir in os.listdir(selected_hash):
                potential_euc_idx = float(euclidean_dir.replace("d", "."))

                if abs(potential_euc_idx - target_euc_idx) <= 0.2:
                    with (selected_hash / euclidean_dir / "idx.txt").open("r") as f:
                        for line in f:
                            id = line.strip()
                            ids.add(id)

        return sorted(ids)

    def get_hash(self, arr):
        """Compute the hash value of the given matrix (each row is an embedding vector)
        with each hash table

        Args:
            arr: The embedding vector (or matrix) to be hashed
        Returns: a matrix of hashes where each row corresponds to the list of hashes
            generated by each hash table for the corresponding vector
            Eg:

            input: each row is a separate embedding vector of length 3
                [
                    [-0.63064807,  0.69387878,  0.13523136],
                    [ 0.92555369,  1.20090607,  0.53282546],
                    [ 0.9797971 ,  0.75951989,  0.38633385],
                    [-1.0376341 ,  0.73896609, -0.58136276],
                    [-0.04855423, -0.06431659, -0.224122  ]
                ]
            output: each row is a list of hashes that were generated
                for the corresponding embedding vector by various hash functions
                (4 hash functions in this example)
                [
                    [[1, 0, 1, 0], [0, 1, 1, 1], [1, 1, 0, 0], [0, 1, 1, 0]],
                    [[1, 1, 0, 1], [0, 0, 0, 1], [1, 0, 1, 0], [0, 0, 0, 0]],
                    [[0, 1, 0, 1], [1, 1, 0, 1], [0, 0, 1, 1], [1, 1, 0, 0]],
                    [[0, 0, 0, 1], [0, 0, 0, 1], [0, 1, 0, 1], [0, 0, 0, 1]],
                    [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [1, 0, 0, 0]]
                ]

            So, the hashes for
                [-0.63064807,  0.69387878,  0.13523136]
            are
                [[1, 0, 1, 0], [0, 1, 1, 1], [1, 1, 0, 0], [0, 1, 1, 0]]
            where
                [1, 0, 1, 0] is generated by the first hash function
                [0, 1, 1, 1] is generated by the second hash function
                [1, 1, 0, 0] is generated by the third hash function
                [0, 1, 1, 0] is generated by the fourth hash function
        """
        dim = np.ndim(arr)

        if dim == 1:
            arr = np.expand_dims(arr, axis=0)

        hashes = [[] for _ in range(arr.shape[0])]

        for hash_table_filename in os.listdir(self.hash_dir):
            hash_table = np.load(self.hash_dir / hash_table_filename)
            hash_mat = np.matmul(arr, hash_table)

            for row_num, row in enumerate(hash_mat):
                bit_hash = []
                for num in row:
                    if num > 0:
                        bit_hash.append("1")
                    else:
                        bit_hash.append("0")
                hashes[row_num].append(int("".join(bit_hash), 2))

        if dim == 1:
            return np.squeeze(hashes, axis=0)
        return hashes

    def l2(self, arr):
        return np.linalg.norm(arr)

    def euclidean(self, arr1, arr2):
        dist = 0
        for a1, a2 in zip(arr1, arr2):
            dist = dist + (a1 - a2) ** 2
        return dist ** 0.5

    def get_euclidean_index(self, arr):
        L2 = self.l2(arr)
        return str(round(L2, 1)).replace(".", "d")

    def _save_params(self):
        """ saves params to the file <index_dir>/params.json """
        with self.params_file.open("w") as f:
            json.dump(self._params, f, indent=4, sort_keys=True)

    def _generate_hash_tables(self):
        """generates and saves each hash table in its own file
        Eg:
            <index_dir>/hash_tables/ht0.npy
            <index_dir>/hash_tables/ht1.npy
            .
            .
            .
            <index_dir>/hash_tables/ht<num_tables>.npy
        """

        for table_num in range(self._params["num_tables"]):
            np.save(
                (self.hash_dir / "ht{}.npy".format(table_num)),
                np.random.randn(
                    self._params["embedding_size"], self._params["hash_size"]
                ),
            )


class SQLDiskLSH:
    """
    Disk based (with SQL) Locality Sensitive Hashing using Random Projection with Multiple hash tables
    """

    def __init__(self):
        self.hash_tables = self._get_hash_tables()

    def add(self, session, id, arr):
        """Index the given vector (or matrix) by calculating and storing the hash
        in one of the buckets

        If arr is a matrix then each row must correspond to an embedding vector
        """
        hashes = self.get_hash(arr)
        unqiue_hashes = set(hashes)

        for hash_bucket in unqiue_hashes:
            hash_bucket = str(hash_bucket)
            euclidean_index = self.get_euclidean_index(arr)

            db_row = Index(
                vec_id=str(id), hash_bucket=hash_bucket, euc_bucket=euclidean_index
            )
            commit_add_db_row(session, db_row)

    def query(self, session, mapper, arr, k=10):
        """
        mapper is a function which takes id as input and gives the
        encoding vector as output
        """
        matches = MinKList(k)

        local_ids = self.get_local_ids(session, arr)
        print("Found {} potential matches".format(len(local_ids)))

        for id_num, l_id in enumerate(local_ids):
            encoding_vec = mapper(l_id)
            dist = self.euclidean(arr, encoding_vec)

            matches.insert(ENCDIST(l_id, dist))

            print(".", end="")
            if id_num % 100 == 0:
                print()

        return sorted(matches.get_items())

    def get_local_ids(self, session, arr):
        """returns the ids that are present in the same hash bucket
        for the given encoding vector
        """

        euclidean_bucket = self.get_euclidean_index(arr)
        similar_euc_buckets = self._get_similar_euclidean_buckets(euclidean_bucket)

        hashes = self.get_hash(arr)
        hashes = list(map(str, hashes))

        unique_hashes = list(set(hashes))

        potential_matches = (
            session.query(Index.vec_id)
            .filter(
                and_(
                    Index.hash_bucket.in_(unique_hashes),
                    Index.euc_bucket.in_(similar_euc_buckets),
                )
            )
            .all()
        )

        potential_matches = [x[0] for x in potential_matches]

        return sorted(set(potential_matches))

    def get_hash(self, arr):
        """Compute the hash value of the given matrix (each row is an embedding vector)
        with each hash table

        Args:
            arr: The embedding vector (or matrix) to be hashed
        Returns: a matrix of hashes where each row corresponds to the list of hashes
            generated by each hash table for the corresponding vector
            Eg:

            input: each row is a separate embedding vector of length 3
                [
                    [-0.63064807,  0.69387878,  0.13523136],
                    [ 0.92555369,  1.20090607,  0.53282546],
                    [ 0.9797971 ,  0.75951989,  0.38633385],
                    [-1.0376341 ,  0.73896609, -0.58136276],
                    [-0.04855423, -0.06431659, -0.224122  ]
                ]
            output: each row is a list of hashes that were generated
                for the corresponding embedding vector by various hash functions
                (4 hash functions in this example)
                [
                    [[1, 0, 1, 0], [0, 1, 1, 1], [1, 1, 0, 0], [0, 1, 1, 0]],
                    [[1, 1, 0, 1], [0, 0, 0, 1], [1, 0, 1, 0], [0, 0, 0, 0]],
                    [[0, 1, 0, 1], [1, 1, 0, 1], [0, 0, 1, 1], [1, 1, 0, 0]],
                    [[0, 0, 0, 1], [0, 0, 0, 1], [0, 1, 0, 1], [0, 0, 0, 1]],
                    [[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [1, 0, 0, 0]]
                ]

            So, the hashes for
                [-0.63064807,  0.69387878,  0.13523136]
            are
                [[1, 0, 1, 0], [0, 1, 1, 1], [1, 1, 0, 0], [0, 1, 1, 0]]
            where
                [1, 0, 1, 0] is generated by the first hash function
                [0, 1, 1, 1] is generated by the second hash function
                [1, 1, 0, 0] is generated by the third hash function
                [0, 1, 1, 0] is generated by the fourth hash function
        """
        dim = np.ndim(arr)

        if dim == 1:
            arr = np.expand_dims(arr, axis=0)

        hashes = [[] for _ in range(arr.shape[0])]

        for hash_table in self.hash_tables:
            hash_mat = np.matmul(arr, hash_table)

            for row_num, row in enumerate(hash_mat):
                bit_hash = []
                for num in row:
                    if num > 0:
                        bit_hash.append("1")
                    else:
                        bit_hash.append("0")
                hashes[row_num].append(int("".join(bit_hash), 2))

        if dim == 1:
            return np.squeeze(hashes, axis=0)
        return hashes

    def l2(self, arr):
        return np.linalg.norm(arr)

    def euclidean(self, arr1, arr2):
        dist = 0
        for a1, a2 in zip(arr1, arr2):
            dist = dist + (a1 - a2) ** 2
        return dist ** 0.5

    def get_euclidean_index(self, arr):
        L2 = self.l2(arr)
        return str(round(L2, 1)).replace(".", "d")

    def _get_similar_euclidean_buckets(self, euc_bucket, n=2):
        euc_bucket_num = round(float(euc_bucket.replace("d", ".")), 1)

        similar = [euc_bucket]
        for i in range(1, n + 1):
            s = euc_bucket_num - (0.1 * i)
            s = round(s, 1)
            s = str(s).replace(".", "d")
            similar.append(s)

            s = euc_bucket_num + (0.1 * i)
            s = round(s, 1)
            s = str(s).replace(".", "d")
            similar.append(s)

        return similar

    def _get_hash_tables(self):
        with SessionCM() as session:
            results = session.query(HashTables).all()

        # if the index database already contains hashtables
        # then just return them
        if results:
            hash_tables = [
                np.zeros(shape=(EMBEDDING_SIZE, HASH_SIZE)) for _ in range(NUM_TABLES)
            ]

            for htno, i, j, val in results:
                hash_tables[htno][i][j] = val

            return hash_tables

        # if the index database doesn't contain hashtables,
        # then generate the hashtables, store them in db and return them
        else:
            hash_tables = [
                np.random.randn(EMBEDDING_SIZE, HASH_SIZE) for _ in range(NUM_TABLES)
            ]

            with SessionCM() as session:
                for htno, htable in hash_tables:
                    for i in htable.shape[0]:
                        for j in htable.shape[1]:
                            val = hash_tables[htno][i][j]
                            db_row = HashTables(htno, i, j, val)

                            commit_add_db_row(session, db_row)

            return hash_tables
