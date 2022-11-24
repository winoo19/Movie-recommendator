import pandas as pd
import re
import warnings
import os


warnings.filterwarnings("ignore")


def get_director(element):
    element = list(filter(lambda el: el["job"] == "Director", element))
    if not element:
        return ""
    else:
        return element[0]["name"]


def parse_to_list(element):
    l = []
    for el in element:
        l.append(el["name"])
    return l


def parse_cast_to_list(element):
    l = []
    for el in element[:5]:
        l.append(el["name"])
    return l


def filter_by_name(df: pd.DataFrame, name: str):
    for word in name.split():
        df = df[df["title"].str.contains(rf"\b{word}\b", flags=re.IGNORECASE)]
    return df


def get_similarity(movie: pd.DataFrame):
    def similarity(movie_to_compare: pd.DataFrame):
        score = []
        if movie["title"] == movie_to_compare["title"]:
            return []

        score.append(0.1 if movie["adult"] == movie_to_compare["adult"] else 0)

        score.append(0.3*len(set(movie["genres"]) & set(movie_to_compare["genres"])))

        or_length = len(set(movie["keywords"]) | set(movie_to_compare["keywords"]))

        if or_length == 0:
            score.append(0)
        else:
            score.append(5*len(set(movie["keywords"]) & set(movie_to_compare["keywords"]))/\
                len(set(movie["keywords"]) | set(movie_to_compare["keywords"])))

        score.append(0.15*len(set(movie["cast"]) & set(movie_to_compare["cast"])))

        score.append(0.2 if abs(movie["release_date"].year-movie_to_compare["release_date"].year) < 30 else 0)

        score.append(0.2 if movie["director"] == movie_to_compare["director"] else 0)

        score.append(movie_to_compare["vote_average"]/8 if movie_to_compare["popularity"] > 4 else 0)

        return score
    return similarity


def parse_movies(movies: pd.DataFrame, keywords: pd.DataFrame, credits: pd.DataFrame):
    movies = movies.drop_duplicates("title")
    movies = movies[["adult", "genres", "id", "original_language", "overview", "popularity", "production_companies", "release_date", "title", "vote_average"]]

    movies = movies.dropna(subset=["original_language", "title", "popularity", "production_companies", "release_date", "vote_average"])
    movies = movies.fillna("")

    movies = movies.astype({"adult": bool,
                            "id": int,
                            "original_language": str,
                            "overview": str,
                            "popularity": float,
                            "title": str,
                            "vote_average": float})
    movies["genres"] = movies["genres"].map(eval)
    movies["production_companies"] = movies["production_companies"].map(eval)
    movies["release_date"] = pd.to_datetime(movies["release_date"])

    movies.index = movies["id"]
    movies = movies.drop(columns=["id"])
    movies = movies.sort_index()


    keywords["keywords"] = keywords["keywords"].map(eval)

    keywords.index = pd.to_numeric(keywords["id"])
    keywords = keywords.drop(columns=["id"])


    credits.index = pd.to_numeric(credits["id"])
    credits = credits.drop(columns=["id"])
    credits["cast"] = credits["cast"].map(eval)
    credits["crew"] = credits["crew"].map(eval)


    movies = movies.merge(keywords, left_index=True, right_index=True)
    movies = movies.merge(credits, left_index=True, right_index=True)

    movies["director"] = movies["crew"].map(get_director)
    movies = movies.drop(columns=["crew"])

    movies["genres"] = movies["genres"].map(parse_to_list)
    movies["production_companies"] = movies["production_companies"].map(parse_to_list)
    movies["keywords"] = movies["keywords"].map(parse_to_list)
    movies["cast"] = movies["cast"].map(parse_cast_to_list)

    return movies


def parse_datatypes(movies: pd.DataFrame):
    movies = movies.astype({"adult": bool,
                        "id": int,
                        "original_language": str,
                        "overview": str,
                        "popularity": float,
                        "title": str,
                        "vote_average": float})

    movies["genres"] = movies["genres"].map(eval)
    movies["production_companies"] = movies["production_companies"].map(eval)
    movies["keywords"] = movies["keywords"].map(eval)
    movies["cast"] = movies["cast"].map(eval)
    movies["release_date"] = pd.to_datetime(movies["release_date"])
    
    return movies


if __name__ == "__main__":
    if os.path.exists("parsed_movies.csv"):
        movies = pd.read_csv("parsed_movies.csv")
        movies = parse_datatypes(movies)
    else:
        movies = pd.read_csv("movies_metadata.csv")
        keywords = pd.read_csv("keywords.csv")
        credits = pd.read_csv("credits.csv")

        movies = parse_movies(movies, keywords, credits)
        movies.to_csv("parsed_movies.csv")

    finished = False
    while not finished:
        os.system("cls|clear")
        movie = pd.DataFrame()
        while movie.empty:
            movie = input("Select movie to recommend on: ")
            movie = filter_by_name(movies, movie)
            if movie.empty:
                print("No match found, try again\n")
        movie.index = range(movie.shape[0])

        if movie.shape[0] > 1:
            print(movie["title"], "\n")
            correct_selection = False
            while not correct_selection:
                try:
                    selection = input("Input the index of the desired movie: ")
                    selection = movie.iloc[int(selection)]
                except:
                    print("Invalid input\n")
                else:
                    correct_selection = True
            movie = selection
        else:
            movie = movie.iloc[0]

        movies["similarity_des"] = movies.apply(get_similarity(movie), axis=1)
        movies["similarity"] = movies["similarity_des"].map(sum)
        movies = movies.sort_values(by="similarity", ascending=False)
        print(movies[["title", "vote_average", "popularity", "genres", "keywords", "similarity", "similarity_des"]].head(5))

        finished = input("Do you want another recommendation? (y/n): ")
        if finished == "y":
            finished = False
        else:
            finished = True
