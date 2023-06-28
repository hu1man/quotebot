const TelegramBot = require('node-telegram-bot-api');
const request = require('request');
const { exec } = require('child_process');

const botToken = '5996289644:AAGW-xIVLh7J4JAI54Pp9KON66AuAHARYvY';  // Replace with your bot token
const bot = new TelegramBot(botToken, { polling: true });

const backgrounds = [
  {
    name: 'Gradient 1',
    image: 'base64_encoded_image_1',
  },
  {
    name: 'Gradient 2',
    image: 'base64_encoded_image_2',
  },
  // Add more backgrounds as needed
];

// Handler for the start command
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;

  // Create custom keyboard with buttons for each background
  const keyboard = {
    keyboard: backgrounds.map((bg) => [bg.name]),
    one_time_keyboard: true,
  };

  // Send initial message with background options
  bot.sendMessage(chatId, 'Select a background:', { reply_markup: keyboard });
});

// Handler for when a background is selected
bot.onText(/\/background (.+)/, (msg, match) => {
  const chatId = msg.chat.id;
  const selectedBackground = match[1];

  // Find the selected background image
  const background = backgrounds.find((bg) => bg.name === selectedBackground);

  if (!background) {
    bot.sendMessage(chatId, 'Invalid background selection.');
    return;
  }

  // Send the background image to the user
  bot.sendPhoto(chatId, Buffer.from(background.image, 'base64'));
  bot.sendMessage(chatId, 'Enter your quote:');
});

// Handler for when a quote is entered
bot.onText(/^(?!\/).+/, (msg) => {
  const chatId = msg.chat.id;
  const quote = msg.text;

  // Replace the path with the actual path to quote_generator.py
  const scriptPath = 'bot.py';

  // Execute the quote generator script
  exec(`python ${scriptPath} "${quote}"`, (error, stdout) => {
    if (error) {
      console.error(`Error executing Python script: ${error}`);
      bot.sendMessage(chatId, 'An error occurred. Please try again.');
      return;
    }

    const quoteImage = stdout.trim();

    // Send the generated quote image to the user
    bot.sendPhoto(chatId, Buffer.from(quoteImage, 'base64'));
  });
});
