#!/bin/bash
echo "🌐 Public IP Info:"
curl -s http://ip-api.com/json/ | jq -r '
"IP: \(.query)
ISP: \(.isp)
City: \(.city)
Region: \(.regionName)
Country: \(.country)
Lat/Lon: \(.lat), \(.lon)
"'
