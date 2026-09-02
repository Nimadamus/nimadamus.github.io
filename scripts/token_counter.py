def count_tokens(text, max_tokens=200):
    if len(text.split()) > max_tokens:
        return True
    else:
        return False

def truncate_text(text, max_tokens=200):
    tokens = text.split()
    if len(tokens) > max_tokens:
        return ' '.join(tokens[:max_tokens])
    else:
        return text