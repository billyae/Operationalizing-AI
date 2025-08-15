# Operationalizing-AI

Mini Projects of Duke AIPI561 - LLMops   

Team members: Zihao Yang, Reina Shi, Yiqing Liu

All the projects were completed by team together.

Final Repo: https://github.com/billyae/AIPI561-Final-Project


## Mini Projects in each folder
 
Week1: Conversational AI Assistant powered by Amazon Bedrock. 
Week2: AI Orchestration Pipeline with Amazon Bedrock.  
Week3: Enterprise Bedrock Chatbot.     
Week4: Multi-Modal AI Service.  
Week5: Application Development with Bedrock.    
Week6: Responsible AI and Security. 


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
