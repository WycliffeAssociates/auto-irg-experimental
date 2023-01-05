import json


def getLanguages():
    f = open('/app/languages.json')
    return json.load(f)


def getBooks():
    f = open('/app/books.json')
    return json.load(f)
