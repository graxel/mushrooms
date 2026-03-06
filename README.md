# mushrooms

This is an example of a complete, end-to-end MLOps pipeline run on local hardware.

I got a free-use dataset of poisonous and edible mushrooms and their characteristics from [where I got mushrooms from]. Here's a peak at the data:
    table of data



My home lab setup consists of a Raspberry Pi 5 and an old Dell XPS laptop. The RPi5 is used as the main orchestration server, and the laptop is used as a database backend. The RPi5 will query data from the database and serve it to my website, [here](kevingrazel.com/mushrooms.html)
