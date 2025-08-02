#!/bin/bash
API_KEY="YOUR_API_KEY"
CITY="Karachi"  # Change to your city
echo "🌤️ Weather in $CITY:"
curl -s "http://api.openweathermap.org/data/2.5/weather?q=$CITY&appid=$API_KEY&units=metric" | jq -r '.main.temp, .weather[0].description'
