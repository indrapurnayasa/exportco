# Prompt Logging System for Chatbot

## Overview

The prompt logging system tracks which prompts are selected by the chatbot for each user interaction. This provides valuable insights into prompt performance, usage patterns, and helps optimize the prompt library.

## Features

### 1. **Automatic Prompt Usage Logging**
- Logs every prompt selection with detailed information
- Updates usage count in the database
- Tracks similarity scores and response types
- Provides comprehensive audit trail

### 2. **Usage Count Tracking**
- Automatically increments `usage_count` field in `prompt_library` table
- Updates `updated_at` timestamp when prompt is used
- Maintains accurate usage statistics

### 3. **Detailed Logging Information**
- **Prompt ID**: Which prompt was selected
- **User Query**: The original user question (truncated for privacy)
- **Similarity Score**: How well the prompt matched the query
- **Response Type**: Context of usage (chatbot, document_query, etc.)
- **Timestamp**: When the prompt was used

## Implementation

### 1. **Prompt Library Service Enhancement**

```python
async def log_prompt_usage(self, prompt_id: int, user_query: str, similarity: float, response_type: str = "chatbot"):
    """
    Log prompt usage and update usage count
    """
    try:
        # Update usage count
        stmt = update(PromptLibrary).where(PromptLibrary.id == prompt_id).values(
            usage_count=PromptLibrary.usage_count + 1,
            updated_at=datetime.utcnow()
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Log the usage
        logger.info(f"[PROMPT USAGE] Prompt ID: {prompt_id}, Query: '{user_query[:100]}...', Similarity: {similarity:.3f}, Type: {response_type}")
        
    except Exception as e:
        logger.error(f"Error logging prompt usage: {e}")
```

### 2. **Integration Points**

The logging is integrated at key points in the chatbot system:

#### **Main Chatbot Endpoint**
```python
# When prompt is selected
if result:
    prompt, similarity = result
    await service.log_prompt_usage(prompt.id, query, similarity, "chatbot")
else:
    # Default prompt
    await service.log_prompt_usage(0, query, similarity, "default_prompt")
```

#### **Dynamic Prompt Selection**
```python
# When dynamic prompt is found
if result:
    prompt, similarity = result
    await service.log_prompt_usage(prompt.id, query, similarity, "dynamic_prompt")
else:
    # Default dynamic prompt
    await service.log_prompt_usage(0, query, 0.0, "default_dynamic_prompt")
```

## Log Output Examples

### 1. **Successful Prompt Selection**
```
[PROMPT USAGE] Prompt ID: 1, Query: 'Hitung bea keluar untuk ekspor CPO 1000 kg ke India...', Similarity: 0.850, Type: chatbot
```

### 2. **Default Prompt Usage**
```
[PROMPT USAGE] Prompt ID: 0, Query: 'Apa kabar?...', Similarity: 0.000, Type: default_prompt
```

### 3. **Document Query**
```
[PROMPT USAGE] Prompt ID: 2, Query: 'Dokumen apa saja yang diperlukan untuk ekspor ke Tiongkok?...', Similarity: 0.920, Type: document_query
```

## Database Schema

### **Prompt Library Table**
```sql
CREATE TABLE prompt_library (
    id SERIAL PRIMARY KEY,
    prompt_template TEXT NOT NULL,
    keywords TEXT[],
    embedding VECTOR(1536),
    usage_count INTEGER DEFAULT 0,  -- Tracks usage
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()  -- Updated on usage
);
```

## Usage Analytics

### 1. **View Most Used Prompts**
```sql
SELECT id, prompt_template, usage_count, updated_at 
FROM prompt_library 
ORDER BY usage_count DESC;
```

### 2. **View Recent Prompt Usage**
```sql
SELECT id, prompt_template, usage_count, updated_at 
FROM prompt_library 
WHERE updated_at > NOW() - INTERVAL '24 hours'
ORDER BY updated_at DESC;
```

### 3. **Prompt Performance Analysis**
```sql
SELECT 
    id,
    usage_count,
    ROUND(usage_count * 100.0 / SUM(usage_count) OVER (), 2) as usage_percentage
FROM prompt_library 
WHERE is_active = true
ORDER BY usage_count DESC;
```

## Testing

### **Run Test Script**
```bash
python examples/test_prompt_logging.py
```

### **Expected Output**
```
🧪 Testing Prompt Logging...

📝 Test Case 1:
   Prompt ID: 1
   Query: 'Hitung bea keluar untuk ekspor CPO 1000 kg ke India'
   Similarity: 0.850
   Type: chatbot
   ✅ Logged successfully

📝 Test Case 2:
   Prompt ID: 2
   Query: 'Dokumen apa saja yang diperlukan untuk ekspor ke Tiongkok?'
   Similarity: 0.920
   Type: document_query
   ✅ Logged successfully

📊 Checking Updated Usage Counts...
   Prompt ID 1: 1 uses
   Prompt ID 2: 1 uses

✨ Prompt logging test completed!
```

## Benefits

### 1. **Performance Monitoring**
- Track which prompts are most effective
- Identify underutilized prompts
- Monitor similarity score distributions

### 2. **Quality Assurance**
- Audit trail for prompt selections
- Debug prompt selection issues
- Validate similarity thresholds

### 3. **Optimization Insights**
- Identify high-performing prompts
- Find prompts that need improvement
- Understand user query patterns

### 4. **Analytics**
- Usage statistics for reporting
- Prompt effectiveness metrics
- User behavior analysis

## Configuration

### **Logging Level**
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### **Custom Logging**
You can extend the logging to include additional information:

```python
# Add custom fields
logger.info(f"[PROMPT USAGE] Prompt ID: {prompt_id}, Query: '{user_query[:100]}...', Similarity: {similarity:.3f}, Type: {response_type}, User: {user_id}, Session: {session_id}")
```

## Future Enhancements

### 1. **Separate Usage Table**
Create a dedicated table for detailed usage tracking:

```sql
CREATE TABLE prompt_usage_logs (
    id SERIAL PRIMARY KEY,
    prompt_id INTEGER REFERENCES prompt_library(id),
    user_query TEXT,
    similarity FLOAT,
    response_type VARCHAR(50),
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2. **Analytics Dashboard**
- Real-time prompt usage statistics
- Performance metrics visualization
- A/B testing for prompt variations

### 3. **Automated Optimization**
- Auto-disable low-performing prompts
- Suggest prompt improvements
- Dynamic threshold adjustment

## Troubleshooting

### **Common Issues**

1. **Logging Not Working**
   - Check database connection
   - Verify prompt ID exists
   - Check logging configuration

2. **Usage Count Not Updating**
   - Check database permissions
   - Verify transaction commits
   - Check for constraint violations

3. **Performance Issues**
   - Monitor database performance
   - Consider async logging
   - Implement batch updates

## Security Considerations

### 1. **Data Privacy**
- Truncate user queries in logs (max 100 characters)
- Don't log sensitive information
- Implement log rotation

### 2. **Access Control**
- Restrict access to usage logs
- Implement audit logging
- Secure database connections

### 3. **Compliance**
- Follow data protection regulations
- Implement data retention policies
- Provide data export capabilities 