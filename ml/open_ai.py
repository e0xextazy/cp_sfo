import openai


openai.api_key = ''
system_msg = "Вы превосходный AI помощник."


def get_description(post_text):
    post_text = f"Что такое {post_text}."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": post_text},
        ],
    )

    return response.choices[0].message.content
