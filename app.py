import gradio as gr
import os
from dotenv import load_dotenv
from voice_clone import VoiceClone
from voice2text import AudioTranscriber
from split_vedio2audio import VideoAudioSplitter
from voice_generate import VoiceGenerator

load_dotenv()

# 初始化 API key
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
voice_clone = VoiceClone(SILICONFLOW_API_KEY)
transcriber = AudioTranscriber(SILICONFLOW_API_KEY)
video_splitter = VideoAudioSplitter()
voice_generator = VoiceGenerator(SILICONFLOW_API_KEY)

# 定义可用的模型
AVAILABLE_MODELS = {
    "CosyVoice2": "FunAudioLLM/CosyVoice2-0.5B",
    "Fish Speech": "fishaudio/fish-speech-1.5",
    "GPT-SoVITS": "RVC-Boss/GPT-SoVITS"
}

# 定义内置声音
built_in_voices = ["alex", "anna", "bella", "benjamin", "charles", "claire", "david", "diana"]

def process_voice_clone(audio_file, reference_text, target_text, model_choice, voice_id):
    """处理语音克隆请求"""
    if not audio_file or not reference_text or not target_text:
        return "请确保所有必填字段都已填写", None

    try:
        # 上传参考音频
        model_id = AVAILABLE_MODELS[model_choice]
        result = voice_clone.upload_voice_base64(
            audio_file.name,
            voice_id,
            model_id,
            reference_text
        )

        if not result or 'uri' not in result:
            return "上传音频失败", None

        voice_uri = result['uri']

        # 生成输出音频文件路径
        output_dir = os.path.join("outputs", model_choice)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"output_{voice_id}.wav")

        # 生成克隆语音
        voice_clone.speech(
            target_text,
            voice=voice_uri,
            model_id=model_id,
            speech_file_path=output_path
        )

        return "语音克隆成功完成！", output_path

    except Exception as e:
        return f"处理过程中出错: {str(e)}", None

def transcribe_audio(audio_file):
    """处理语音转文字请求"""
    if not audio_file:
        return "请上传音频文件"

    try:
        print(audio_file)  # audio_file is already a path string
        result = transcriber.transcriptions(audio_file)
        return result.get('text', '转写失败')
    except Exception as e:
        return f"转写过程中出错: {str(e)}"

def split_video_audio(video_file, start_time=None, duration=None):
    """处理视频分离音频请求"""
    if not video_file:
        return "请上传视频文件", None

    try:
        # 处理视频分离
        output_path = video_splitter.split_video_to_audio(
            video_file,
            start_time,
            duration
        )
        return "音频提取成功！", output_path
    except Exception as e:
        return f"处理过程中出错: {str(e)}", None

def generate_speech(text, model_choice, voice, speed, gain, response_format, sample_rate):
    """处理语音合成请求"""
    if not text:
        return "请输入要合成的文本", None
    
    try:
        # 生成输出音频文件路径
        output_dir = "outputs/generated"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"generated_{os.urandom(4).hex()}.wav")
        
        # 生成语音
        model_id = AVAILABLE_MODELS[model_choice]
        speech_data = voice_generator.create_speech(
            text,
            model=model_id,
            voice=voice,
            speed=speed,
            gain=gain,
            response_format=response_format,
            sample_rate=sample_rate
        )
        
        # 保存音频文件
        with open(output_path, "wb") as f:
            f.write(speech_data)
            
        return "语音合成成功！", output_path
    except Exception as e:
        return f"处理过程中出错: {str(e)}", None

def refresh_voice_list():
    """刷新语音列表"""
    return gr.Dropdown(choices=voice_generator.get_voice_list())

def delete_voice(voice):
    """删除语音"""
    if not voice:
        return "请选择要删除的语音", None
    
    try:
        voice_uri = voice.split(':', 1)[-1]
        result = voice_generator.delete_voice(voice_uri)
        print("删除结果：", result)
        if result == "success":
            return "语音删除成功！", gr.Dropdown(choices=voice_generator.get_voice_list())
        else:
            return f"删除失败：{result.get('message', '未知错误')}", None
    except Exception as e:
        return f"删除过程中出错: {str(e)}", None

# 创建 Gradio 界面
with gr.Blocks(title="数字人工具包") as demo:
    gr.Markdown("# 🎤 数字人工具包")

    with gr.Tabs():
        # 视频分离音频标签页
        with gr.Tab("视频分离音频"):
            with gr.Row():
                with gr.Column():
                    video_input = gr.Video(label="上传视频文件")
                    start_time = gr.Textbox(
                        label="开始时间（格式：HH:MM:SS，例如 00:01:30）",
                        placeholder="00:00:00"
                    )
                    duration = gr.Textbox(
                        label="持续时间（格式：HH:MM:SS，例如 00:00:30）",
                        placeholder="00:00:00"
                    )
                    split_btn = gr.Button("开始分离", variant="primary")

                with gr.Column():
                    split_status = gr.Textbox(label="处理状态")
                    output_audio_file = gr.Audio(label="提取的音频")

        # 语音转写标签页
        with gr.Tab("语音转写"):
            audio_input_transcribe = gr.Audio(label="上传要转写的音频", type="filepath")
            transcribe_btn = gr.Button("开始转写", variant="primary")
            transcription_output = gr.Textbox(label="转写结果")
            
        # 语音克隆标签页
        with gr.Tab("语音克隆"):
            with gr.Row():
                with gr.Column():
                    audio_input = gr.Audio(label="上传参考音频", type="filepath")
                    reference_text = gr.Textbox(label="参考音频文本", placeholder="请输入参考音频对应的文本内容")
                    target_text = gr.Textbox(label="目标生成文本", placeholder="请输入要生成的文本内容")
                    model_choice = gr.Dropdown(
                        choices=list(AVAILABLE_MODELS.keys()),
                        label="选择模型",
                        value="CosyVoice2"
                    )
                    voice_id = gr.Textbox(
                        label="声音ID",
                        value="voice_" + os.urandom(4).hex(),
                        placeholder="请输入唯一的声音ID"
                    )
                    clone_btn = gr.Button("开始克隆", variant="primary")

                with gr.Column():
                    output_message = gr.Textbox(label="处理状态")
                    output_audio = gr.Audio(label="生成的音频")

        # 语音合成标签页
        with gr.Tab("语音合成"):
            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(
                        label="输入文本",
                        placeholder="请输入要合成的文本内容",
                        lines=5
                    )
                    model_select = gr.Dropdown(
                        choices=list(AVAILABLE_MODELS.keys()),
                        label="选择模型",
                        interactive=True,
                        value="CosyVoice2"
                    )
                    voice_select = gr.Dropdown(
                        choices=built_in_voices + voice_generator.get_voice_list(),
                        label="选择声音",
                        interactive=True,
                        value=built_in_voices[0]
                    )
                    with gr.Row():
                        response_format = gr.Dropdown(
                            choices=["mp3", "opus", "wav", "pcm"],
                            label="输出格式",
                            value="wav"
                        )
                        sample_rate = gr.Dropdown(
                            choices=[8000, 16000, 24000, 32000, 44100, 48000],
                            info="opus: Supports 48000 Hz. wav, pcm: Supports 8000, 16000, 24000, 32000, 44100 Hz, with a default of 44100 Hz. mp3: Supports 32000, 44100 Hz, with a default of 44100 Hz.",
                            label="采样率",
                            value=44100
                        )
                        speed_slider = gr.Slider(
                            minimum=0.25,
                            maximum=4.0,
                            value=1.0,
                            step=0.1,
                            label="语速"
                        )
                        gain_slider = gr.Slider(
                            minimum=-20,
                            maximum=20,
                            value=0,
                            step=1,
                            label="音量增益"
                        )
                    generate_btn = gr.Button("开始合成", variant="primary")

                with gr.Column():
                    generate_status = gr.Textbox(label="处理状态")
                    generated_audio = gr.Audio(label="合成的音频")

        # 语音管理标签页
        with gr.Tab("语音管理"):
            with gr.Row():
                with gr.Column():
                    voice_list = gr.Dropdown(
                        choices=voice_generator.get_voice_list(),
                        label="选择要删除的语音",
                        interactive=True
                    )
                    with gr.Row():
                        refresh_btn = gr.Button("刷新列表", variant="secondary")
                        delete_btn = gr.Button("删除语音", variant="primary")
                with gr.Column():
                    manage_status = gr.Textbox(label="处理状态")

    # 绑定事件
    clone_btn.click(
        process_voice_clone,
        inputs=[audio_input, reference_text, target_text, model_choice, voice_id],
        outputs=[output_message, output_audio]
    )

    transcribe_btn.click(
        transcribe_audio,
        inputs=[audio_input_transcribe],
        outputs=[transcription_output]
    )

    split_btn.click(
        split_video_audio,
        inputs=[video_input, start_time, duration],
        outputs=[split_status, output_audio_file]
    )

    generate_btn.click(
        generate_speech,
        inputs=[text_input, model_select, voice_select, speed_slider, gain_slider, response_format, sample_rate],
        outputs=[generate_status, generated_audio]
    )

    refresh_btn.click(
        refresh_voice_list,
        outputs=[voice_list]
    )

    delete_btn.click(
        delete_voice,
        inputs=[voice_list],
        outputs=[manage_status, voice_list]
    )

if __name__ == "__main__":
    demo.launch(share=True)
