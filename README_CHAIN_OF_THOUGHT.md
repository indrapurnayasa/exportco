# Chain of Thought (CoT) untuk Chatbot ExportMate

## Overview

Chain of Thought (CoT) adalah teknik AI yang memaksa model untuk berpikir step-by-step sebelum memberikan jawaban. Implementasi ini meningkatkan akurasi dan kualitas response chatbot dengan menganalisis query user secara sistematis.

## 🧠 **Fitur Chain of Thought**

### 1. **Analisis Query Terstruktur**
- Identifikasi intent dengan confidence score
- Ekstraksi data otomatis (negara, produk, berat, dll)
- Validasi kelengkapan data
- Perencanaan response yang tepat

### 2. **Intent Classification**
- **document_list**: Daftar dokumen ekspor
- **document_template**: Template dokumen spesifik
- **export_duty**: Perhitungan bea keluar
- **general_info**: Informasi umum ekspor
- **data_extraction**: Ekstraksi data dari query

### 3. **Response Generation dengan CoT**
- Review analisis sebelumnya
- Plan response structure
- Format response yang konsisten
- Validate response quality

## 🔧 **Implementasi**

### 1. **Chain of Thought Service**

```python
class ChainOfThoughtService:
    async def analyze_query_with_cot(self, user_query: str, context: str = "") -> Dict:
        """
        Menganalisis query user menggunakan Chain of Thought
        """
```

### 2. **Analisis Step-by-Step**

```python
# Langkah-langkah analisis CoT:
1. IDENTIFIKASI INTENT
   - Apa yang sebenarnya ingin diketahui user?
   - Apakah ini pertanyaan tentang dokumen ekspor?
   - Apakah ini pertanyaan tentang bea keluar/pajak?

2. ANALISIS KONTEKS
   - Negara mana yang disebutkan?
   - Produk/komoditas apa yang disebutkan?
   - Dokumen apa yang diminta?

3. KLASIFIKASI JENIS RESPONSE
   - Document List, Template, Export Duty, dll

4. VALIDASI DATA
   - Apakah semua data yang diperlukan sudah lengkap?
   - Data apa yang masih kurang?

5. RENCANA RESPONSE
   - Response apa yang akan diberikan?
   - Template dokumen mana yang akan ditampilkan?
```

### 3. **Integration dengan Chatbot**

```python
# Step 1: Analyze query with Chain of Thought
cot_analysis = await cot_service.analyze_query_with_cot(query)

# Step 2: Handle different intents based on CoT analysis
intent = cot_analysis['intent']

# Step 3: Generate response using Chain of Thought
cot_response = await cot_service.generate_response_with_cot(
    user_query=query,
    analysis=cot_analysis,
    prompt_template=prompt.prompt_template
)
```

## 📊 **Output Analysis**

### **Format JSON Analysis**
```json
{
    "intent": "export_duty",
    "confidence": 0.95,
    "extracted_data": {
        "country": "India",
        "product": "CPO",
        "weight": 1000,
        "document_type": null,
        "currency": null
    },
    "missing_data": [],
    "reasoning": "User meminta perhitungan bea keluar dengan data lengkap",
    "response_plan": "Hitung bea keluar dan tampilkan hasil perhitungan",
    "requires_template": false,
    "template_type": null
}
```

### **Response dengan CoT**
```json
{
    "answer": "Berdasarkan analisis query Anda...",
    "analysis": {...},
    "cot_used": true,
    "generated_at": "2024-01-15T10:30:00Z"
}
```

## 🧪 **Testing**

### **Run Test Script**
```bash
python examples/test_chain_of_thought.py
```

### **Expected Output**
```
🧠 Testing Chain of Thought Analysis...

📝 Test Case 1: Export duty calculation
   Query: 'Hitung bea keluar untuk ekspor CPO 1000 kg ke India'
   Expected Intent: export_duty
   ✅ Analysis completed!
   Actual Intent: export_duty
   Confidence: 0.950
   Reasoning: User meminta perhitungan bea keluar dengan data lengkap...
   🎯 Intent match: YES
   📊 Extracted Data:
      country: India
      product: CPO
      weight: 1000

📝 Test Case 2: Document list request
   Query: 'Dokumen apa saja yang diperlukan untuk ekspor ke Tiongkok?'
   Expected Intent: document_list
   ✅ Analysis completed!
   Actual Intent: document_list
   Confidence: 0.920
   Reasoning: User meminta daftar dokumen ekspor...
   🎯 Intent match: YES
   📊 Extracted Data:
      country: Tiongkok
```

## 🎯 **Contoh Penggunaan**

### 1. **Export Duty Calculation**
```
Input: "Hitung bea keluar untuk ekspor CPO 1000 kg ke India"

CoT Analysis:
- Intent: export_duty (confidence: 0.95)
- Extracted: country=India, product=CPO, weight=1000
- Missing: none
- Plan: Calculate export duty and show results

Output: Detailed calculation with step-by-step explanation
```

### 2. **Document Template Request**
```
Input: "Tolong buatkan invoice untuk pengiriman ke Bangladesh"

CoT Analysis:
- Intent: document_template (confidence: 0.88)
- Extracted: country=Bangladesh, document_type=invoice
- Missing: product details, weight
- Plan: Show invoice template

Output: Invoice template with fillable fields
```

### 3. **General Information**
```
Input: "Negara mana saja yang menjadi tujuan ekspor utama Indonesia?"

CoT Analysis:
- Intent: general_info (confidence: 0.92)
- Extracted: none specific
- Missing: none
- Plan: Provide general export destination information

Output: Comprehensive list of main export destinations
```

## 🔍 **Keunggulan CoT**

### 1. **Akurasi yang Lebih Tinggi**
- Analisis sistematis mengurangi kesalahan
- Confidence score membantu validasi
- Fallback mechanism untuk error handling

### 2. **Response yang Lebih Terstruktur**
- Step-by-step reasoning
- Konsistensi dalam format response
- Penjelasan yang lebih jelas

### 3. **Debugging yang Lebih Mudah**
- Audit trail lengkap
- Analisis yang transparan
- Error tracking yang detail

### 4. **Scalability**
- Mudah menambah intent baru
- Flexible response planning
- Modular architecture

## 📈 **Performance Monitoring**

### **CoT Metrics**
```python
# Log CoT performance
logger.info(f"[COT] Analysis completed: {analysis['intent']} with confidence {analysis['confidence']}")
logger.info(f"[COT] Generating response with prompt ID: {prompt.id}")
```

### **Response Quality**
- Confidence score tracking
- Intent accuracy monitoring
- Response generation success rate
- Execution time measurement

## 🔧 **Configuration**

### **OpenAI Settings**
```python
# CoT Analysis
temperature=0.1,  # Low temperature for consistent analysis
max_tokens=1000   # Sufficient for detailed analysis

# Response Generation
temperature=0.7,  # Balanced creativity and consistency
max_tokens=800    # Appropriate response length
```

### **Threshold Settings**
```python
# Confidence threshold
confidence_threshold = 0.7

# Similarity threshold for prompt selection
similarity_threshold = 0.7
```

## 🚀 **Future Enhancements**

### 1. **Advanced Reasoning**
- Multi-step reasoning chains
- Context memory across conversations
- Learning from user feedback

### 2. **Intent Expansion**
- More specific intents
- Sub-intent classification
- Dynamic intent detection

### 3. **Response Optimization**
- A/B testing for response formats
- User satisfaction tracking
- Automated response improvement

### 4. **Integration Features**
- Real-time learning
- Custom prompt templates
- Advanced analytics dashboard

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **Low Confidence Scores**
   - Check prompt quality
   - Review training data
   - Adjust thresholds

2. **Intent Misclassification**
   - Improve keyword extraction
   - Add more training examples
   - Refine intent definitions

3. **Response Quality Issues**
   - Review prompt templates
   - Check context relevance
   - Validate response format

### **Debug Commands**
```python
# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

# Test specific query
analysis = await cot_service.analyze_query_with_cot("test query")
print(json.dumps(analysis, indent=2))
```

## 📚 **Best Practices**

### 1. **Prompt Engineering**
- Use clear, specific instructions
- Include examples when possible
- Maintain consistency across prompts

### 2. **Error Handling**
- Implement graceful fallbacks
- Log all errors for debugging
- Provide user-friendly error messages

### 3. **Performance Optimization**
- Cache frequently used analyses
- Batch similar queries
- Monitor API usage and costs

### 4. **Quality Assurance**
- Regular testing with diverse queries
- Monitor confidence score distributions
- Collect user feedback for improvement

## 🎉 **Benefits Summary**

✅ **Improved Accuracy**: Systematic analysis reduces errors
✅ **Better User Experience**: More relevant and structured responses
✅ **Enhanced Debugging**: Transparent reasoning process
✅ **Scalable Architecture**: Easy to extend and maintain
✅ **Quality Monitoring**: Comprehensive metrics and logging
✅ **Flexible Integration**: Works with existing prompt library system 