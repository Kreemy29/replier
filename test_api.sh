#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing Reply Generation API${NC}\n"

# Test data
TEST_DATA='{
  "original": {
    "username": "user1",
    "text": "Just finished a 10K run and feeling amazing!"
  },
  "target": {
    "username": "user2",
    "text": "That's awesome! I'm training for a half marathon next month."
  },
  "history": [
    {
      "username": "user3",
      "text": "Great job! What was your time?"
    }
  ]
}'

echo -e "${GREEN}1. Testing POST /generate-reply${NC}"
echo "Sending request..."
TASK_ID=$(curl -s -X POST "http://localhost:8000/generate-reply" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA" | jq -r '.task_id')

if [ -z "$TASK_ID" ]; then
    echo -e "${RED}Failed to get task ID${NC}"
    exit 1
fi

echo "Task ID: $TASK_ID"
echo -e "\n${GREEN}2. Testing GET /generate-reply/{task_id}${NC}"

# Poll for the result
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Polling attempt $((RETRY_COUNT + 1))..."
    RESULT=$(curl -s "http://localhost:8000/generate-reply/$TASK_ID")
    STATUS=$(echo "$RESULT" | jq -r '.status')
    
    if [ "$STATUS" == "done" ]; then
        echo -e "${GREEN}Success!${NC}"
        echo "Reply: $(echo "$RESULT" | jq -r '.reply')"
        exit 0
    elif [ "$STATUS" == "failure" ]; then
        echo -e "${RED}Task failed: $(echo "$RESULT" | jq -r '.error')${NC}"
        exit 1
    fi
    
    echo "Status: $STATUS"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

echo -e "${RED}Timeout waiting for task completion${NC}"
exit 1 