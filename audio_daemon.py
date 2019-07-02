import os
import time
import argparse
import boto3
import pyaudio
import subprocess
import glog as log
import config
import tempfile
import wave
from pydub import AudioSegment


class AudioRecorder:
    def __init__(self,
                 interval=1,
                 duration=5,
                 output_path='/tmp/',
                 upload_to_s3=False):
        self.NUM_SEGMENTS_UNTIL_UPLOAD = 10
        self._output_path = output_path
        self._interval = interval - duration
        self._duration = duration
        self._audio = pyaudio.PyAudio()
        self._audio_device_id = self._get_device_id()
        # Container for audio segments.
        self._segments = []

        if upload_to_s3:
            s3 = boto3.resource('s3')
            self._bucket = s3.Bucket(config.BUCKET_NAME)
        else:
            self._bucket = None

    def spin(self):
        while True:
            if not self.process():
                break
            time.sleep(self._interval)

    def process(self):
        print "Recording..."
        self._segments.append(self._record_stream())
        if len(self._segments) >= self.NUM_SEGMENTS_UNTIL_UPLOAD:
            segment = self._join_segments(self._segments)
            self._segments = []
            timestamp = long(time.time())
            basename = '{}.mp3'.format(timestamp)
            local_filename = os.path.join(self._output_path, basename)
            self._save_mp3(segment, local_filename)
            print "Saved {}".format(local_filename)
            self._upload(local_filename)
        return True

    def _join_segments(self, segments):
        FADE_DURATION_SECONDS = 1.0
        CROSSFADE_DURATION_SECONDS = 0.1
        output = None
        for segment in segments:
            if output is None:
                output = segment
            else:
                output = output.append(
                    segment, crossfade=int(CROSSFADE_DURATION_SECONDS * 1000))
        output = output.fade_in(int(FADE_DURATION_SECONDS * 1000)).fade_out(
            int(FADE_DURATION_SECONDS * 1000))
        return output

    def _get_device_id(self):
        TARGET_DEVICE_NAME = 'HD Webcam C525'
        for i in range(self._audio.get_device_count()):
            info = self._audio.get_device_info_by_index(i)
            if TARGET_DEVICE_NAME in info['name']:
                return i
        assert "Could not find target audio device"
        return -1

    def _record_stream(self):
        input_device_index = 7
        rate = 48000 / 2
        chunk = 1024
        stream = self._audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=rate,
            input=True,
            input_device_index=self._audio_device_id,
            frames_per_buffer=chunk)
        all = []
        for i in range(0, int(rate / chunk * float(self._duration))):
            data = stream.read(chunk, exception_on_overflow=False)
            all.append(data)
        stream.stop_stream()
        stream.close()
        data = b''.join(all)
        wav_filename = tempfile.mkstemp()[1] + '.wav'
        wv = wave.open(wav_filename, 'wb')
        wv.setnchannels(1)
        wv.setframerate(rate)
        wv.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
        wv.writeframes(data)
        wv.close()
        audio = AudioSegment.from_wav(wav_filename)
        os.remove(wav_filename)
        return audio

    def _save_mp3(self, data, mp3_filename):
        wav_filename = tempfile.mkstemp()[1] + '.wav'
        data.export(wav_filename, format='wav')
        cmd = ['lame', '--preset', 'phone', wav_filename, mp3_filename]
        subprocess.check_call(cmd)
        os.remove(wav_filename)

    def _upload(self, local_filename):
        log.info("Uploading {} to S3".format(local_filename))
        if self._bucket is not None:
            try:
                remote_filename_key = os.path.join('audio', 'latest.mp3')
                log.info("Uploading to s3 ({})".format(remote_filename_key))
                self._bucket.upload_file(local_filename, 
                                         remote_filename_key,
                                         ExtraArgs={
                                             'ACL': "public-read",
                                             'ContentType': "audio/mpeg",
                                             })
                # Don't remove -- we may need these images elsewhere, and
                # it's expensive to download them back from S3.
                #os.remove(output_filename)
            except Exception as error:
                log.error(error)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--interval',
        default=config.AUDIO_PERIOD_SEC,
        type=int,
        help='Capture interval')
    parser.add_argument(
        '--duration',
        default=config.AUDIO_DURATION_SEC,
        type=int,
        help='Capture duration')
    parser.add_argument(
        '--device_id', default=0, type=int, help='Camera device id')
    parser.add_argument(
        '--output_path', default=config.LOCAL_CACHE_DIR, help='Output path')
    parser.add_argument(
        '--no-upload',
        default=False,
        action='store_true',
        help='Do not upload to S3?')

    args = parser.parse_args()
    log.check_le(args.duration, args.interval)
    upload = True if not args.no_upload else False

    recorder = AudioRecorder(
        interval=args.interval,
        duration=args.duration,
        output_path=args.output_path,
        upload_to_s3=upload)
    recorder.spin()


if __name__ == "__main__":
    main()
