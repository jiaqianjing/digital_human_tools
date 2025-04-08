import requests
import json

class VoiceGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1/audio"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def get_voice_list(self):
        """获取语音列表"""
        url = f"{self.base_url}/voice/list"
        response = requests.get(url, headers=self.headers).json()
        return [f"{item['customName']}:{item['uri']}" for item in response['result']]

    def delete_voice(self, uri):
        """删除指定的语音"""
        url = f"{self.base_url}/voice/deletions"
        data = {"uri": uri}
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()

    def create_speech(self, text, voice, model="FunAudioLLM/CosyVoice2-0.5B",
                     speed=1, gain=0, sample_rate=24000):
        """生成语音"""
        url = f"{self.base_url}/speech"
        data = {
            "input": text,
            "response_format": "wav",
            "stream": True,
            "speed": speed,
            "gain": gain,
            "model": model,
            "voice": voice.split(':', 1)[-1] if ":" in voice else f"{model}:{voice}",
            "sample_rate": sample_rate
        }
        print(f"生成语音请求数据：{data}")
        response = requests.post(url, headers=self.headers, json=data)
        return response.content  # 返回音频二进制数据

