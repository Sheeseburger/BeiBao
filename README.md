# BeiBao
# Automatic clothes selector from user's wardrobe

## Welcome to BeiBao
>This is the final project of [CS50x](https://cs50.harvard.edu/x/2020/). It is a web application that helps you manage own virtual wardrobe.
> Project was created by @Sheeseburger and @annabellehere
## Explaining the project and the database
Our final project is a website that allow the user to:
1. Add clothes to wardrobe.
    - Remove it.
    - Pack it to virtual backpack.
2. Add clothes as item to "wannabuy".
    - Remove it.
    - Add it to wardrobe.
3. Generate outfit,that matches user's temperature.
    - Save outfit to favourite.
4. Create own outfit.
5. Look in

### Database:
We needed five tables for our database:

- First table Users. Simple table for storing info about users.

- Second table is Item. It stores correct information for choosing clothes type. It is done by us.

- Third table is Users_Item. It stores information about every user's clothes.

- Fourth table is Users_Outfits. It stores information about user's outfits.

- Fifth table is Outfits_Item. It manages to merge multiple items into one outfit.

<img src="https://imgur.com/mRgRyGV.jpg">

## Logo and brand name
> BeiBao is translated from China as backpack.

| Logo |
| :---: |
| <img src="https://i.imgur.com/FiPxkhP.jpg"> |

## User Instruction
### Running flask
> Before running flask, you need to export **WEATHER_API_KEY**, you need to sign up on openweathermap and make [API key](https://home.openweathermap.org/api_keys)

### Register & Login
> Create a new account by the **"Register"** button on the nav-bar, after you need to sign in and mention your city, so program can make valid API request, if something will go wrong, BeiBao will mention it.

| Register | Login |
| :---: | :---: |
| <img src="https://i.imgur.com/9qT1beU.png">  | <img src="https://i.imgur.com/TXY8296.png">|

### Homepage and Backpack
> Homepage is basicly your virtual wardrobe.
> Backpack is portable virtual wardrobe.

| Homepage | Backpack |
| :---: |  :---: |
| <img src="https://i.imgur.com/YbDclRo.png">| <img src="https://i.imgur.com/M1sM3GY.png">|
| <img src="https://i.imgur.com/4OZU8ns.png">| <img src="https://i.imgur.com/BUIOYJ9.png">|

### Add item and wannabuy
> They are have same script, but when user add item to wannabuy list, it will take less time and won't display in the **Homepage**.
> When item is loaded python script remove background,save image into /static/items via unic and save filename.

| Add page | Wannabuy page |
| :---: |  :---: |
| <img src="https://i.imgur.com/ZZUSPFe.png">| <img src="https://i.imgur.com/U1pLz1c.png">|

### Outfit generator and creator
> User can both generate outfit or creat own.(Note: Generator will be based on temperature )

| Generate page | Create page |
| :---: |  :---: |
| <img src="https://i.imgur.com/RglMIlp.png">| <img src="https://i.imgur.com/6pcPr7m.png">|

### Outfit page and trend
> Outfit page is similar to homepage.
> Trend page is showing fashion instagram account.

| Outfit page | Trend page |
| :---: |  :---: |
| <img src="https://i.imgur.com/pdSfc8J.png">| <img src="https://i.imgur.com/gUBNOw1.png">|
| <img src="https://i.imgur.com/Pm8Lhvd.png">| <img src="https://i.imgur.com/toMWiP7.png">|

## Demonstration on youtube
For the CS50 final project you have to make a video showning your project,
[My Final Project presentation](https://youtu.be/m4K8QW97niE)

## Documentation
https://flask.palletsprojects.com/en/1.1.x/

https://numpy.org/doc/

https://openweathermap.org/current

## Features

- [Openweathermap API](https://openweathermap.org/)
- [Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [OpenCV](https://flask-wtf.readthedocs.io/en/stable/index.html)

We've used API for requesting user's temperature to correctly generate outfits,moreover if the weather will be rain,program will try to add windblower to your look at least.
