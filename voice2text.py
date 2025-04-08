import requests
import os

class AudioTranscriber:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.siliconflow.cn/v1/audio/transcriptions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "multipart/form-data; boundary=---011000010111000001101001"
        }
    
    def transcriptions(self, audio_file_path):
        """
        将音频文件转换为文字
        
        Args:
            audio_file_path (str): 音频文件的路径
            
        Returns:
            dict: API 响应的结果
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_file_path}")
            
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'file': ('audio.wav', audio_file, 'audio/wav'),
                'model': (None, 'FunAudioLLM/SenseVoiceSmall')
            }
            
            try:
                response = requests.post(
                    self.url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                raise Exception(f"API 请求失败: {str(e)}")
