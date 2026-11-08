"""
Diverse joke database with multiple categories for natural humor.
"""

import random

# Joke categories with varied humor
JOKES = {
    "dad_jokes": [
        "Why don't eggs tell jokes? They'd crack each other up!",
        "I'm reading a book about anti-gravity. It's impossible to put down!",
        "What do you call a fake noodle? An impasta!",
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "I used to hate facial hair, but then it grew on me.",
        "What do you call a bear with no teeth? A gummy bear!",
        "Why can't you give Elsa a balloon? Because she will let it go!",
        "I told my wife she was drawing her eyebrows too high. She looked surprised.",
        "What's the best thing about Switzerland? I don't know, but the flag is a big plus.",
        "Why did the bicycle fall over? Because it was two-tired!",
        "I'm on a seafood diet. I see food and I eat it!",
        "What do you call cheese that isn't yours? Nacho cheese!",
        "Why couldn't the leopard play hide and seek? Because he was always spotted!",
        "I used to play piano by ear, but now I use my hands.",
        "How do you organize a space party? You planet!",
        "What do you call a lazy kangaroo? A pouch potato!",
        "I told my computer I needed a break, and now it won't stop sending me Kit-Kat ads.",
        "Why do cows have hooves instead of feet? Because they lactose!",
        "What's brown and sticky? A stick!",
        "I'm afraid for the calendar. Its days are numbered.",
    ],
    "puns": [
        "I told my wife she should embrace her mistakes. She gave me a hug.",
        "A backward poet writes inverse.",
        "I wondered why the frisbee was getting bigger. Then it hit me.",
        "What do you call a belt made of watches? A waist of time!",
        "I used to be a banker, but I lost interest.",
        "The rotation of Earth keeps me spinning.",
        "I asked the librarian if they had books on paranoia. She whispered, 'They're right behind you!'",
        "I got fired from the calendar factory. All I did was take a day off!",
        "What do you call a fish without eyes? A fsh!",
        "I'm so good with puzzles I could put the whole world together.",
        "Why do bees have sticky hair? Because they use honeycombs!",
        "I told a chemistry joke. There was no reaction.",
        "What do you call a sleeping dinosaur? A dino-snore!",
        "I couldn't figure out how to put my seatbelt on. Then it clicked.",
        "Why don't skeletons fight each other? They don't have the guts!",
    ],
    "animal": [
        "What do you call an alligator in a vest? An investigator!",
        "Why do seagulls fly over the sea? Because if they flew over the bay, they'd be bagels!",
        "What do you call a dog that does magic tricks? A Labracadabrador!",
        "Why don't oysters share? Because they're shellfish!",
        "What do you call a cow with no legs? Ground beef!",
        "What do you call a cow with two legs? Lean beef!",
        "Why do fish live in salt water? Because pepper makes them sneeze!",
        "What do you call a pig that does karate? A pork chop!",
        "Why do chickens lay eggs? Because if they dropped them, they'd break!",
        "What do you get when you cross a snowman with a vampire? Frostbite!",
        "What do you call a deer with no eyes? No idea!",
        "What do you call a deer with no eyes and no legs? Still no idea!",
        "Why do goats make the best musicians? Because they have great goat horns!",
        "What do you call a sleeping bull? A bulldozer!",
        "What do you call a frog that jumps really well? The rest of the frogs!",
    ],
    "food": [
        "What do you call a sad strawberry? A blueberry!",
        "Why did the tomato turn red? Because it saw the salad dressing!",
        "What do you call a lazy spud? A potato!",
        "Why did the coffee file a police report? It got mugged!",
        "What do you call a snowman with a six-pack? An abdominal snowman!",
        "Why did the banana go to the doctor? Because it wasn't peeling well!",
        "What do you call a dinosaur that crashes their car? Tyrannosaurus Wrecks!",
        "Why did the grape stop in the middle of the road? Because it ran out of juice!",
        "What do you call a cow that magic tricks? A labracadabracow!",
        "Why did the melon jump into the lake? It wanted to be a watermelon!",
        "What do you call a can of beans that's been dropped? A sardine!",
        "Why did the bread win the race? Because it was a loaf winner!",
        "What do you call a fake noodle in a relationship? An impasta couple!",
        "Why did the cookie go to the hospital? Because it felt crummy!",
        "What do you call a cheese that doesn't belong to you? Nacho cheese!",
    ],
    "one_liners": [
        "I told my wife she was improvising. She made a note of it.",
        "Parallel lines have so much in common. It's a shame they'll never meet.",
        "I threw a boomerang a few years ago. I now live in constant fear.",
        "My wife told me to stop impersonating a flamingo. I had to put my foot down.",
        "I have a joke about time travel, but you didn't like it.",
        "I have a joke about construction, but I'm still working on it.",
        "I have a joke about a train, but it's going to be a minute.",
        "I have a joke about a broom, but it's pretty sweeping.",
        "I have a joke about a scarecrow, but it's too outstanding.",
        "I have a joke about a piece of paper, but it's too tearable.",
        "I have a joke about a piece of string, but it's tied up.",
        "I have a joke about a piece of chalk, but it's too elementary.",
        "I have a joke about a piece of wood, but it's too bark-worthy.",
        "I have a joke about a piece of glass, but it's too shattering.",
        "I have a joke about a piece of metal, but it's too rusty.",
    ],
    "knock_knock": [
        "Knock knock. Who's there? Nobel. Nobel who? Nobel... that's why I stood in the corner!",
        "Knock knock. Who's there? Tank. Tank who? You're welcome!",
        "Knock knock. Who's there? Honey bee. Honey bee who? Honey bee a dear and get me a drink!",
        "Knock knock. Who's there? Lettuce. Lettuce who? Lettuce in, it's cold out here!",
        "Knock knock. Who's there? Interrupting cow. Interrupting cow wh— JUST KIDDING!",
        "Knock knock. Who's there? Boo. Boo who? Don't cry, it's just a joke!",
        "Knock knock. Who's there? Apple. Apple who? Apple what you had for lunch?",
        "Knock knock. Who's there? Olive. Olive who? Olive you and I don't want to lose you!",
        "Knock knock. Who's there? Atch. Atch who? Bless you!",
        "Knock knock. Who's there? Dishes. Dishes who? Dishes a very bad joke!",
    ],
    "observational": [
        "I have a lot of jokes about unemployed people, but none of them work.",
        "My dog used to chase people on a bike a lot. It got so bad I had to take his bike away.",
        "I invented a new word today: Plagiarism!",
        "I have a joke about the Titanic. Now I'm sinking into silence.",
        "I have a joke about a broken pencil, but it's pointless.",
        "I have a joke about a broken clock, but it's too late.",
        "I have a joke about a broken mirror, but it would be shattered.",
        "I have a joke about a broken record, but it would go on and on.",
        "I have a joke about a broken elevator, but it would take you down.",
        "I have a joke about a broken ladder, but it would fall apart.",
    ],
    "clever": [
        "I read a sign that said 'Watch for Children.' I thought, 'But I am not a child!'",
        "I read a sign that said 'Slow, Children Playing.' I thought, 'What are they playing so slowly?'",
        "I read a sign that said 'No Trespassing.' I thought, 'I'm not trespassing, I'm just standing here.'",
        "I read a sign that said 'No Loitering.' I thought, 'I'm not loitering, I'm just waiting.'",
        "I read a sign that said 'No Parking.' I thought, 'I'm not parking, I'm just stopping.'",
        "I read a sign that said 'No Entry.' I thought, 'I'm not entering, I'm just looking.'",
        "I read a sign that said 'No Smoking.' I thought, 'I'm not smoking, I'm just thinking.'",
        "I read a sign that said 'No Swimming.' I thought, 'I'm not swimming, I'm just wading.'",
        "I read a sign that said 'No Fishing.' I thought, 'I'm not fishing, I'm just casting.'",
        "I read a sign that said 'No Hunting.' I thought, 'I'm not hunting, I'm just observing.'",
    ],
    "wordplay": [
        "I'm reading a book about teleportation. I can't put it down, but I can't hold it either.",
        "I'm reading a book about time travel. It's going backwards and forwards at the same time.",
        "I'm reading a book about mirrors. It's a reflection on modern society.",
        "I'm reading a book about gravity. It's a real page-turner.",
        "I'm reading a book about anti-matter. It's impossible to put down.",
        "I'm reading a book about the ocean. It's a little salty.",
        "I'm reading a book about the desert. It's a little dry.",
        "I'm reading a book about the jungle. It's a little wild.",
        "I'm reading a book about the mountains. It's a little steep.",
        "I'm reading a book about the forest. It's a little dense.",
    ],
    "silly": [
        "What's orange and sounds like a monkey? A gorilla!",
        "What's red and bad for your teeth? A brick!",
        "What's green and stays out all night? A lime in jail!",
        "What's yellow and polite? A lemon!",
        "What's blue and not very heavy? Light blue!",
        "What's white and made of glass? A window!",
        "What's brown and sticky? A stick!",
        "What's black and white and read all over? A newspaper!",
        "What's red and bad for your teeth? A brick!",
        "What's green and smells like pepper spray? A bull in a garden!",
    ],
    "science": [
        "Why can you never trust an atom? Because they make up everything!",
        "What did the biologist wear on a first date? Designer jeans!",
        "What's a tree's favorite drink? Woodpepper!",
        "Why did the photon refuse the hotel room? Because it was traveling light!",
        "What did the ocean say to the beach? Nothing, it just waved.",
        "Why did the chemist break up with his girlfriend? He got tired of argon!",
        "What did the biologist wear on a first date? Designer jeans!",
        "Why did the DNA cross the road? To get to the other stranded!",
        "What's a physicist's favorite food? Fission chips!",
        "Why did the electron break up with the proton? It didn't feel attracted!",
    ],
    "work": [
        "I told my boss three companies were after me and I needed a raise. We laughed and shook hands. I don't know why he was laughing.",
        "I told my boss I needed a raise because three companies were after me. He asked which ones. I said delivery companies.",
        "My boss told me to have a seat, so I sat down and waited. He's still waiting.",
        "I work 9 to 5, but I'm not a morning person. I'm a 'I need coffee' person.",
        "I told my boss I was going on a diet. He said, 'Don't come to work hungry.'",
        "My boss said, 'Dress for the job you want, not the job you have.' So I wore pajamas to the CEO's office.",
        "I told my boss I needed a raise. He said, 'Take this envelope and go home.' I thought I was fired, but it was full of money!",
        "My boss told me to throw away the weak tea. I thought he was firing me.",
        "I told my boss I was going to start a side business. He said, 'What kind?' I said, 'A business where I tell you what kind.'",
        "My boss said, 'If you don't shape up, you're going to ship out.' I said, 'I'm already shaped up.' He said, 'No, you're shaped out.'",
    ],
    "relationships": [
        "My wife accused me of being immature. I said, 'You're the one who's always blaming me!'",
        "I asked my wife what she wanted for her birthday. She said, 'Nothing, just surprise me.' So I gave her nothing.",
        "My wife told me to stop singing 'Wonderwall.' I said maybe...",
        "I told my wife she was drawing her eyebrows too high. She looked surprised.",
        "My wife asked me to stop impersonating a flamingo. I had to put my foot down.",
        "I asked my wife if she had any sense. She said, 'At least enough to know you don't.'",
        "My wife said I never listen to her. Or something like that.",
        "I told my wife I was going to start a family. She said, 'You mean the one we already have?'",
        "My wife asked me why I was staring at her. I said, 'I was wondering if you were as beautiful as our wedding photo.' She said, 'I was wondering if you were as blind as our wedding photo.'",
        "My wife said I'm always on my phone. I said, 'At least I'm not always on my phone.' She said, 'You are right now.'",
    ],
    "self_deprecating": [
        "I have a joke about my appearance, but I don't want to be mean.",
        "I have a joke about my intelligence, but I don't want to be honest.",
        "I have a joke about my cooking, but it's too burnt.",
        "I have a joke about my driving, but it's too crash-worthy.",
        "I have a joke about my singing, but it's too off-key.",
        "I have a joke about my dancing, but it's too clumsy.",
        "I have a joke about my fashion sense, but it's too outdated.",
        "I have a joke about my sense of humor, but it's too unfunny.",
        "I have a joke about my memory, but I'll forget it.",
        "I have a joke about my patience, but I don't have time.",
    ],
    "dark_humor": [
        "I have a joke about unemployment, but it doesn't work.",
        "I have a joke about a broken pencil, but it's pointless.",
        "I have a joke about a broken clock, but it's too late.",
        "I have a joke about a broken mirror, but it's too shattering.",
        "I have a joke about a broken record, but it goes on and on.",
        "I have a joke about a broken elevator, but it takes you down.",
        "I have a joke about a broken ladder, but it falls apart.",
        "I have a joke about a broken bridge, but it's too collapsed.",
        "I have a joke about a broken chain, but it's too linked.",
        "I have a joke about a broken promise, but it's too empty.",
    ],
    "kids": [
        "Why did the kid bring a ladder to school? Because he wanted to go to high school!",
        "Why did the kid bring a pencil to bed? Because he wanted to draw his dreams!",
        "Why did the kid bring a ruler to school? Because he wanted to measure up!",
        "Why did the kid bring a map to school? Because he wanted to find his way!",
        "Why did the kid bring a flashlight to school? Because he wanted to brighten the day!",
        "Why did the kid bring a clock to school? Because he wanted to be on time!",
        "Why did the kid bring a book to school? Because he wanted to read!",
        "Why did the kid bring a pencil to school? Because he wanted to write!",
        "Why did the kid bring a eraser to school? Because he wanted to make mistakes!",
        "Why did the kid bring a backpack to school? Because he wanted to carry his stuff!",
    ],
    "technology": [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why did the developer go broke? Because he used up all his cache!",
        "What's a programmer's favorite hangout place? Foo Bar!",
        "Why do Java developers wear glasses? Because they can't C#!",
        "I changed my password to 'incorrect' so when I forget it, the computer tells me: 'Your password is incorrect.'",
        "There are only 10 types of people in the world: those who understand binary and those who don't.",
        "A SQL query walks into a bar, sees two tables, and asks: 'Can I JOIN you?'",
        "Why do programmers always mix up Halloween and Christmas? Because Oct 31 == Dec 25!",
        "What's a computer's favorite snack? Microchips!",
        "Why was the computer cold? It left its Windows open!",
    ],
}

# All jokes flattened for quick random access
ALL_JOKES = []
for category_jokes in JOKES.values():
    ALL_JOKES.extend(category_jokes)


def get_joke(category: str = None, exclude: list = None) -> str:
    """
    Get a random joke, optionally filtered by category.
    
    Args:
        category: One of the keys in JOKES dict, or None for any category
        exclude: List of jokes already told (to avoid repeats)
    
    Returns:
        A random joke string
    """
    if category and category in JOKES:
        pool = JOKES[category]
    else:
        pool = ALL_JOKES
    
    # Filter out already-told jokes if possible
    if exclude:
        available = [j for j in pool if j not in exclude]
        if not available:
            available = pool  # Reset if all told
        return random.choice(available)
    
    return random.choice(pool)


def get_joke_categories() -> list:
    """Return list of available joke categories"""
    return list(JOKES.keys())


def get_joke_count(category: str = None) -> int:
    """Return number of jokes in a category or total"""
    if category and category in JOKES:
        return len(JOKES[category])
    return len(ALL_JOKES)
