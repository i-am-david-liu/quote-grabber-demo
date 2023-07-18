# What is this?

This is a Discord bot that grabs a random quote from a database and displays it in chat.

A "quote" is a notable Discord message that is copied and preserved in a dedicated channel (usually called #quotes). This is not standard practice, so it's okay if you're an avid Discord user and have never heard of them.

As a further example, a generic quotes channel would have a structure like this:
```
--- July 8, 2023 ---

[1:22 AM] Bob 
    Alice: a bee crawled into my soda, and then a spider, and I think they're now fighting??

--- July 14, 2023 ---

[5:05 PM] Alice
    Greg: Is the conference today or tomorrow
    Alice: neither?
    Greg: Oh myy god
    Greg: I set my calendar to 2022

--- July 16, 2023 ---

etc, etc
```

# Note to reader

Because this is a Discord bot, running the code **requires a bot token**. As a consequence, I decided to create a little write-up so readers don't have to sign up for a bot account / parse through the code themselves. I am open to showcase a demo using toy databases in the future, however.

Also note that this bot is currently **a work in progress**.

# How it works

A high-level framework:

1. Load the quote database, which is currently a JSON file
2. Load the voting database, which I will detail further below
3. Await for a user command. The two useful commands right now are `!quote`, which tells the bot to output a random quote, and `!rating`, which outputs the rating for a specified quote.

When a user types `!quote`, the bot outputs something like this:

![](https://cdn.discordapp.com/attachments/830105192078770226/1130942573603737651/quotebot_img.png)

The **author** is the user that preserved the quote **message**. The total rating of the message is in bold, with the individual upvotes and downvotes in parentheses. The **message_id** is located at the bottom (the *footer*), and is used as an argument for `!rating` to fetch the appropriate quote.

At the very bottom we have three emojis: upvote, downvote, and remove vote. These elements are called *emoji reactions* in Discord, and can be clicked on by any user. The way it works here is when a user taps one of the reactions under a quote, it sends the corresponding event to the bot, which then updates the voting database accordingly.

## The voting system

Discord assigns a unique identifier to every message and user, so the system is rather simple.

The voting database is accessed through SQLite3. Each row contains three values:

- `message_id`, which represents the unique identifier of the message
- `upvotes`, which represents a list of user ids
- `downvotes`, which is also a list of user ids

The database is updated when a vote is cast. The implication here is that the database *only stores message_id's that have a rating*; it does not store all of the quotes at once. So, if a user asks for the rating of a quote that does not exist in the database, then the rating must be 0.

`upvotes` and `downvotes` store lists so they can keep track of user-specific votes. Using this representation, it's trivial to self-correct when a user tries to upvote *and* downvote at the same time (find duplicates), and we can use the length of each list to compute the total rating.

# Future steps

There's a lot of low-hanging fruit for this bot, so I'll only list the biggest ones:

1. **Use buttons instead of emoji reactions.** Discord recently added [buttons](https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=button#discord.Button) for bots, which are more idiomatic for what I'm trying to accomplish with reactions. In fact, reactions were kludgy workarounds for Discord bots to read message-based events.

2. **Auto-updating the quote database**. There's two ways to do this: either I have the bot "watch" the quotes channel for new quotes, or I have the bot try-fetch new quotes on a schedule.

3. **Quote stats.** It would be interesting to analyze which user stored the most quotes, which user voted the most, etc.

4. **Output a specific quote.** Using the example from the first section, a user could search `!quote "bee and spider soda"`, and the bot would output the relevant quote. This would also allow users to vote on specific quotes.

5. **Custom message id.** Discord message ids are currently 18 digits long, which is overkill for this particular use case. One idea I had was to assign quote ids starting from 0 and incrementing from there. That way, a typical server would only see at most 2 or 3 digit ids.
