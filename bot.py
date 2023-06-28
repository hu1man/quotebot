import telebot
import PIL
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Initialize the Telegram bot
bot_token = '5996289644:AAGW-xIVLh7J4JAI54Pp9KON66AuAHARYvY'  # Replace with your bot token
bot = telebot.TeleBot(bot_token)

# Store user states
user_states = {}


# Sinhala character map to convert Sinhala text to legacy
sinhala_legacy_map = {
    'අ': 'w',
    'ා': '&',
    '‍ෙ': 'f',
    # ... (remaining character mappings)
}


# Handler for the /start command
@bot.message_handler(commands=['start'])
def start(message):
    # Prompt the user to select the language
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton('Sinhala', callback_data='language_sinhala'),
        telebot.types.InlineKeyboardButton('English', callback_data='language_english'),
    )

    # Send the language selection prompt to the user
    bot.send_message(chat_id=message.chat.id, text='Select your language:', reply_markup=keyboard)


# Handler for handling button clicks
@bot.callback_query_handler(func=lambda call: True)
def handle_button_click(call):
    if call.data.startswith('language_'):
        # Extract the selected language from the callback data
        selected_language = call.data.split('_')[1]

        # Update the user's state with the selected language
        user_states[call.from_user.id] = {'language': selected_language}

        if selected_language == 'sinhala':
            # Send "Still Developing..." message and Language select option again
            bot.send_message(chat_id=call.message.chat.id, text='Still Developing...')
            start(call.message)  # Call the start() function again to prompt language selection
        else:
            # Prompt the user to select the gradient
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                telebot.types.InlineKeyboardButton('Gradient 1', callback_data='gradient_gradient1'),
                telebot.types.InlineKeyboardButton('Gradient 2', callback_data='gradient_gradient2'),
            )

            # Send the gradient selection prompt to the user
            bot.send_message(chat_id=call.message.chat.id, text='Select a gradient:', reply_markup=keyboard)

    elif call.data.startswith('gradient_'):
        # Extract the selected gradient from the callback data
        selected_gradient = call.data.split('_')[1]

        # Update the user's state with the selected gradient
        user_states[call.from_user.id]['gradient'] = selected_gradient

        # Prompt the user to enter the quote
        bot.send_message(chat_id=call.message.chat.id, text='Enter your quote:')

        # Register the next step handler to process the quote
        bot.register_next_step_handler(call.message, process_quote)

def process_quote(message):
    # Retrieve the user's state
    user_id = message.from_user.id
    user_state = user_states.get(user_id)

    if user_state:
        # Retrieve the selected language and gradient from the user's state
        selected_language = user_state.get('language')
        selected_gradient = user_state.get('gradient')

        if selected_language and selected_gradient:
            # Retrieve the quote text entered by the user
            quote_text = message.text

            # Convert Sinhala text to legacy
            if selected_language == 'sinhala':
                quote_text = convert_sinhala_to_legacy(quote_text)

            # Retrieve the user's profile photo and username
            user_profile_photos = bot.get_user_profile_photos(user_id).photos
            if user_profile_photos:
                user_profile_photo = user_profile_photos[0][-1].file_id
            else:
                user_profile_photo = None
            username = message.from_user.username

            if user_profile_photo:
                # Download the user's profile photo
                photo_url = f'https://api.telegram.org/file/bot{bot_token}/{user_profile_photo}'
                response = requests.get(photo_url)
                if response.status_code == 200:
                    try:
                        profile_photo = Image.open(BytesIO(response.content)).convert('RGBA')
                    except PIL.UnidentifiedImageError:
                        profile_photo = None
                else:
                    profile_photo = None
            else:
                profile_photo = None

            # Define the font paths for different languages
            font_paths = {
                'sinhala': 'fontt.ttf',
                'english': 'font.ttf'
            }

            # Retrieve the font path based on the selected language
            font_path = font_paths.get(selected_language)

            if font_path:
                # Load the selected gradient image
                gradient_path = f'{selected_gradient}.png'  # Replace with the actual gradient image path
                gradient = Image.open(gradient_path)

                # Create a blank image for the quote
                quote_image = Image.new('RGBA', gradient.size)
                draw = ImageDraw.Draw(quote_image)

                # Define the text properties
                font_size = 20
                font_color = (255, 255, 255)  # White color

                # Load the font
                font = ImageFont.truetype(font_path, font_size, layout_engine=ImageFont.LAYOUT_BASIC)

                # Calculate the dimensions of the quote text and box
                text_width, text_height = draw.textsize(quote_text, font=font)
                padding = 35
                box_width = text_width + 2 * padding
                box_height = text_height + 2 * padding

                # Calculate the position of the quote box
                box_x = (gradient.width - box_width) // 2
                box_y = (gradient.height - box_height) // 2

                # Draw the rounded rectangle as the quote box
                radius = 10
                draw.rounded_rectangle([(box_x, box_y), (box_x + box_width, box_y + box_height)],
                                       radius=radius, fill=(128, 128, 128, 128))

                # Add user profile photo if available
                if profile_photo:
                    # Resize the profile photo to a square
                    photo_size = min(box_height - padding, box_width - padding)
                    profile_photo = profile_photo.resize((photo_size, photo_size))

                    # Create a circular mask for the profile photo
                    mask = Image.new('L', (photo_size, photo_size), 0)
                    draw_mask = ImageDraw.Draw(mask)
                    draw_mask.ellipse((0, 0, photo_size, photo_size), fill=255)

                    # Apply the circular mask to the profile photo
                    profile_photo = profile_photo.convert("RGBA")
                    profile_photo = Image.composite(profile_photo, Image.new('RGBA', profile_photo.size), mask)

                    # Calculate the position of the profile photo
                    photo_x = box_x + (box_width - photo_size) // 2
                    photo_y = box_y - photo_size - padding

                    # Paste the profile photo onto the quote image
                    quote_image.paste(profile_photo, (photo_x, photo_y), mask=profile_photo)

                # Calculate the position of the quote text
                text_x = box_x + padding
                text_y = box_y + padding

                # Draw the quote text
                draw.text((text_x, text_y), quote_text, font=font, fill=font_color, align='center')

                # Composite the quote image on the gradient background
                result = Image.alpha_composite(gradient.convert('RGBA'), quote_image)

                # Save the final image
                result.save('quote.png')

                # Send the quote image to the user
                bot.send_photo(chat_id=message.chat.id, photo=open('quote.png', 'rb'))

            else:
                # Send an error message if the font path is not found
                bot.send_message(chat_id=message.chat.id, text='Error: Font not found for the selected language.')

        else:
            # Send an error message if the language or gradient is not selected
            bot.send_message(chat_id=message.chat.id, text='Error: Language or gradient not selected.')

    else:
        # Send an error message if the user's state is not found
        bot.send_message(chat_id=message.chat.id, text='Error: User state not found.')


def convert_sinhala_to_legacy(sinhala_text):
    legacy_text = ''
    i = 0
    while i < len(sinhala_text):
        if i + 1 < len(sinhala_text) and sinhala_text[i:i+2] in sinhala_legacy_map:
            legacy_text += sinhala_legacy_map[sinhala_text[i:i+2]]
            i += 2
        elif sinhala_text[i] in sinhala_legacy_map:
            legacy_text += sinhala_legacy_map[sinhala_text[i]]
            i += 1
        else:
            legacy_text += sinhala_text[i]
            i += 1

    return legacy_text


# Start the bot
bot.polling()
