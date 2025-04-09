import os
import requests
import base64
import json
from openai import OpenAI
from typing import Optional


class VoiceClone:
    """语音克隆类"""
    
    def __init__(self, api_key: str):
        """
        初始化语音克隆类
        
        Args:
            api_key: SiliconFlow API密钥
        """
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1"
    
    def upload_voice(
        self,
        audio_path: str,
        voice_id: str,
        model_id: str,
        text: str
    ) -> Optional[dict]:
        """
        使用multipart/form-data方式上传语音文件进行克隆
        
        Args:
            audio_path: 音频文件路径
            voice_id: 声音ID
            model_id: 模型ID
            text: 音频对应的文本
            
        Returns:
            响应结果字典
        """
        try:
            # 判断 audio_file 是否存在
            if not os.path.exists(audio_path):
                print(f"音频文件 {audio_path} 不存在")
                return None
            
            # 构建请求URL和headers
            url = f"{self.base_url}/uploads/audio/voice"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建请求数据
            files = {
                "file": open(audio_path, "rb")
            }
            data = {
                "model": model_id,
                "customName": voice_id,
                "text": text
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, files=files, data=data)
            return response.json()
            
        except Exception as e:
            print(f"上传语音文件失败: {str(e)}")
            return None

    def upload_voice_base64(
        self,
        audio_path: str,
        voice_id: str,
        model_id: str,
        text: str
    ) -> Optional[dict]:
        """
        使用base64编码方式上传语音文件进行克隆
        
        Args:
            audio_path: 音频文件路径
            voice_id: 声音ID
            model_id: 模型ID
            text: 音频对应的文本
            
        Returns:
            响应结果字典
        """
        if not os.path.exists(audio_path):
            print(f"音频文件 {audio_path} 不存在")
            return None
        
        # 读取并编码音频文件
        with open(audio_path, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
        
        url = f"{self.base_url}/uploads/audio/voice"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model_id,
            "customName": voice_id,
            "audio": f"data:audio/mpeg;base64,{audio_base64}",
            "text": text
        }
        response = requests.post(url, headers=headers, data=json.dumps(data)).json()
        print(f"上传语音文件响应: {response}")
        if 'code' in response:
            raise Exception(response['message'])
        return response
            

    def speech(
        self,
        text: str,
        voice: str,
        model_id: str = "FunAudioLLM/CosyVoice2-0.5B",
        response_format: str = "wav",
        speech_file_path: str = "speech.wav"
    ) -> None:
        """
        生成语音
        """
        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            with client.audio.speech.with_streaming_response.create(
                model=model_id, # 支持 fishaudio / GPT-SoVITS / CosyVoice2-0.5B 系列模型
                voice=voice, # 用户上传音色名称，参考
                input=text,
                speed=1.0,
                extra_body={"gain": 0},
                response_format=response_format
                ) as response:
                response.stream_to_file(speech_file_path)
            
        except Exception as e:
            print(f"生成语音失败: {str(e)}")
            return None
