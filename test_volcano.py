"""
火山引擎声音复刻API测试脚本
"""
from volcano_voice import VolcanoVoice
import os
import argparse
import time
from dotenv import load_dotenv

def main():
    # 加载环境变量
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="测试火山引擎声音复刻API")
    parser.add_argument("--appid", help="应用ID", default=os.getenv("VOLC_APPID", ""))
    parser.add_argument("--token", help="访问令牌", default=os.getenv("VOLC_TOKEN", ""))
    parser.add_argument("--audio", required=True, help="音频文件路径")
    parser.add_argument("--text", help="参考文本", default=None)
    parser.add_argument("--voice-id", required=True, help="声音ID")
    parser.add_argument("--language", type=int, default=0, help="语言代码（0=中文，1=英文等）")
    parser.add_argument("--tts-text", help="要合成的文本")
    
    args = parser.parse_args()
    
    # 检查必要的参数
    if not args.appid or not args.token:
        print("错误：缺少必要的参数。请提供--appid和--token参数，或在.env文件中设置VOLC_APPID和VOLC_TOKEN环境变量。")
        return
    
    # 创建输出目录
    output_dir = "outputs/test_volcano"
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化火山引擎声音复刻服务
    volcano = VolcanoVoice(args.appid, args.token)
    
    try:
        # 1. 上传音频训练音色
        print(f"上传音频和训练音色 '{args.voice_id}'...")
        result = volcano.clone_voice(
            audio_path=args.audio,
            speaker_id=args.voice_id,
            text=args.text,
            language=args.language
        )
        print(f"上传结果: {result}")
        
        # 2. 获取训练状态
        print("\n等待10秒后检查训练状态...")
        time.sleep(10)
        
        max_attempts = 30
        current_attempt = 0
        
        while current_attempt < max_attempts:
            current_attempt += 1
            print(f"\n[尝试 {current_attempt}/{max_attempts}] 检查音色 '{args.voice_id}' 的训练状态...")
            status = volcano.get_voice_status(args.voice_id)
            print(f"状态: {status}")
            
            if status.get("code") == 0:
                train_status = status.get("train_status")
                if train_status == "succeed":
                    print(f"\n音色 '{args.voice_id}' 训练成功！版本: {status.get('version')}/10")
                    break
                elif train_status == "failed":
                    print(f"\n音色 '{args.voice_id}' 训练失败！原因: {status.get('message', '未知')}")
                    break
            
            print("音色仍在训练中，10秒后再次检查...")
            time.sleep(10)
        
        # 3. 如果提供了合成文本且训练成功，则尝试合成语音
        if args.tts_text and status.get("code") == 0 and status.get("train_status") == "succeed":
            print(f"\n开始合成文本为语音: '{args.tts_text}'")
            output_path = os.path.join(output_dir, f"test_volcano_{args.voice_id}.wav")
            result = volcano.generate_speech(
                text=args.tts_text,
                speaker_id=args.voice_id,
                output_path=output_path,
                language=args.language
            )
            print(f"语音合成成功！已保存到: {output_path}")
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    main() 