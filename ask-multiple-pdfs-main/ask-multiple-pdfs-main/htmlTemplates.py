# Define CSS styles
css = '''
<style>
.chat-message {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
}
.chat-message.user {
    background-color: #2b313e;
}
.chat-message.bot {
    background-color: #475063;
}
.chat-message.user .avatar {
    width: 20%;
}
.chat-message.bot .avatar {
    width: 20%;
}
.chat-message .avatar img {
    max-width: 78px;
    max-height: 78px;
    border-radius: 50%;
    object-fit: cover;
}
.chat-message .message {
    width: 80%;
    padding: 0 1.5rem;
    color: #fff;
}
</style>
'''

# Define your HTML templates with unique avatar classes
bot_template = '''
<div class="chat-message bot">
    <div class="avatar bot-avatar">
        <img src="https://dataconomy.com/wp-content/uploads/2022/12/OpenAI-ChatGPT-New-chatbots-examples-limitations-and-more-6-1536x1009.jpg">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar user-avatar">
        <img src="https://cdn.dribbble.com/users/1937255/screenshots/14588207/media/0d0b9719cb11ea243c7c9a67ac97dc47.png">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

# Rest of your code remains the same
