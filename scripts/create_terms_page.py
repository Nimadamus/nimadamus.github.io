import os

target = os.path.normpath("C:/Users/Nima/nimadamus.github.io/terms.html")
if os.path.exists(target):
    print("terms.html already exists")
    exit(0)

parts = []
parts.append("<!DOCTYPE html>")
parts.append("<html lang=\"en\">")
parts.append("<head>")
