# Operationalizing-AI

Mini Projects and final project of Duke AIPI561 - LLMops   

Team members: Zihao Yang, Reina Shi, Yiqing Liu

All the projects were completed by team together.

Final Repo: https://github.com/billyae/AIPI561-Final-Project


## Progress

5/23/2025: Conversational AI Assistant powered by Amazon Bedrock.  
6/5/2025: AI Orchestration Pipeline with Amazon Bedrock.  
6/15/2025: Enterprise Bedrock Chatbot.     
6/20/2025: Multi-Modal AI Service.  
6/23/2025: Application Development with Bedrock.    
6/23/2025: Responsible AI and Security. 


## Deployment:

week 1:  https://huggingface.co/spaces/yiqing111/AIPI561_project1

week 2:  https://huggingface.co/spaces/yiqing111/aipi_project2

week 3:  https://huggingface.co/spaces/yiqing111/aipi561_project3_1

week 4 :

Please use this command to compare the image and text similarity:

```bash
curl -X POST "https://billyae-Production-AI-Services.hf.space/compare/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_image.jpg" \
     -F "text=a cat sitting on a chair"
```

Please user this command to check the service healthy:

```bash
curl https://billyae-Production-AI-Services.hf.space/health
```  


week 5: https://huggingface.co/spaces/yiqing111/AIPI561_week5    
    
week 6: https://huggingface.co/spaces/billyae/DukeChatbot    
