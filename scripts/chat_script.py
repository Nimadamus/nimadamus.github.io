from token_counter import count_tokens, truncate_text\n\nwhile True:
    user_input = input("Enter your message: ")\n    from existing_chat_script import generate_response\n\nresponse = generate_response(user_input)\n    if count_tokens(response):
        response = truncate_text(response)\n    print(response)