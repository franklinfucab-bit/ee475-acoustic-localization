package org.ee475.beaconloop;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.media.*;
import android.net.Uri;
import android.os.*;
import java.io.*;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class LoopService extends Service {
    public static final String LOAD="load",TOGGLE="toggle",STOP="stop";
    private static final String CHANNEL="beacon_playback";
    public final class LocalBinder extends Binder { public LoopService service(){return LoopService.this;} }
    public interface Listener { void changed(); }
    private final LocalBinder binder=new LocalBinder();
    private final Handler main=new Handler(Looper.getMainLooper());
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private AudioLoader.Audio audio;private AudioTrack track;private AudioManager manager;
    private AudioFocusRequest focus;private boolean focusHeld,foreground,resumeAfterFocus;
    public Listener listener;public boolean loading,playing,normalize;public String title="Default 20 kHz beacon",status="Choose an audio file or use the included beacon";
    public double gain=1.;
    @Override public void onCreate() {
        super.onCreate();manager=(AudioManager)getSystemService(AUDIO_SERVICE);
        normalize=getSharedPreferences("player",0).getBoolean("normalize",false);
        NotificationChannel channel=new NotificationChannel(CHANNEL,"Loop playback",NotificationManager.IMPORTANCE_LOW);
        channel.setSound(null,null);((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).createNotificationChannel(channel);
        focus=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
            .setAudioAttributes(attributes()).setWillPauseWhenDucked(true)
            .setOnAudioFocusChangeListener(change->{
                if(change==AudioManager.AUDIOFOCUS_GAIN){focusHeld=true;if(resumeAfterFocus){resumeAfterFocus=false;playNow();}}
                else if(change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT||change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK){resumeAfterFocus=playing;pauseNow(false);status="Paused by another audio app";publish();}
                else if(change==AudioManager.AUDIOFOCUS_LOSS){resumeAfterFocus=false;pauseNow(true);status="Paused: audio focus lost";publish();}
            },main).build();
    }
    @Override public IBinder onBind(Intent intent){return binder;}
    @Override public int onStartCommand(Intent intent,int flags,int id) {
        if(intent==null)return START_NOT_STICKY;
        String action=intent.getAction();
        if(STOP.equals(action)){pauseNow(true);releaseTrack();stopForeground(STOP_FOREGROUND_REMOVE);foreground=false;stopSelf();publish();}
        else if(LOAD.equals(action)) {foreground();load(intent.getStringExtra("uri"),intent.getStringExtra("name"));}
        else if(TOGGLE.equals(action)){foreground();if(playing)pauseNow(true);else playNow();}
        return START_NOT_STICKY;
    }
    public boolean ready(){return audio!=null;}
    public String details() {
        if(audio==null)return "WAV, MP3 and other formats supported by your phone · mono/stereo · up to 120 s";
        return String.format(Locale.US,"%d Hz · %s · %.3f s\nInfinite PCM loop · %s",audio.rate,audio.channels==1?"Mono":"Stereo",
            audio.frames()/(double)audio.rate,normalize?String.format(Locale.US,"safe gain %+.1f dB",20*Math.log10(gain)):"original level");
    }
    public void setNormalize(boolean value) {
        if(playing||loading)return;normalize=value;releaseTrack();
        gain=audio==null?1.:PcmGain.gain(audio.pcm,normalize);
        getSharedPreferences("player",0).edit().putBoolean("normalize",normalize).apply();
        status="Ready; the next play starts at the beginning";publish();
    }
    private AudioAttributes attributes(){return new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build();}
    private InputStream openSource(String source)throws IOException{
        if(source==null||source.length()==0)return getAssets().open("default-beacon.wav");
        if(source.startsWith("asset:")){
            String name=source.substring(6);
            if(!name.equals("default-beacon.wav")&&!name.equals("gap-beacon.wav"))throw new IOException("Unknown bundled beacon");
            return getAssets().open(name);
        }
        return getContentResolver().openInputStream(Uri.parse(source));
    }
    private void load(String source,String name) {
        if(loading)return;pauseNow(true);releaseTrack();loading=true;status="Loading audio locally…";publish();
        worker.execute(()->{
            try {
                File selected=new File(getFilesDir(),"selected-audio.bin");
                File incoming=new File(getCacheDir(),"incoming-audio.bin");
                File file;
                if("cache".equals(source)&&selected.isFile())file=selected;
                else {
                    InputStream input=openSource(source);
                    if(input==null)throw new IOException("Cannot open the selected file");
                    try(InputStream in=input;OutputStream out=new FileOutputStream(incoming)) {
                        byte[] buffer=new byte[65536];int count,total=0;
                        while((count=in.read(buffer))>=0){total+=count;if(total>64*1024*1024)throw new IOException("Choose an audio file below 64 MB");out.write(buffer,0,count);}
                    }
                    file=incoming;
                }
                AudioLoader.Audio decoded=AudioLoader.decode(file);
                if(file==incoming) {
                    try(InputStream in=new FileInputStream(incoming);OutputStream out=new FileOutputStream(selected)) {
                        byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))>=0)out.write(buffer,0,n);
                    }
                }
                String display=(name==null||name.isEmpty())?"Default 20 kHz beacon":name;
                main.post(()->{
                    audio=decoded;title=display;loading=false;gain=PcmGain.gain(audio.pcm,normalize);status="Ready · looping is always on";
                    getSharedPreferences("player",0).edit().putString("name",title).putBoolean("has_cached",true).apply();
                    if(!playing){stopForeground(STOP_FOREGROUND_REMOVE);foreground=false;}publish();
                });
            } catch(Exception error) {
                main.post(()->{loading=false;status="Unable to load: "+error.getMessage();stopForeground(STOP_FOREGROUND_REMOVE);foreground=false;publish();});
            }
        });
    }
    private void playNow() {
        if(loading||audio==null){status="Choose an audio file first";publish();return;}
        try {
            if(!focusHeld){focusHeld=manager.requestAudioFocus(focus)==AudioManager.AUDIOFOCUS_REQUEST_GRANTED;if(!focusHeld)throw new IOException("Another app is using audio; try again");}
            if(track==null) {
                gain=PcmGain.gain(audio.pcm,normalize);byte[] data=PcmGain.apply(audio.pcm,gain);
                int mask=audio.channels==1?AudioFormat.CHANNEL_OUT_MONO:AudioFormat.CHANNEL_OUT_STEREO;
                int minimum=AudioTrack.getMinBufferSize(audio.rate,mask,AudioFormat.ENCODING_PCM_16BIT);
                track=new AudioTrack.Builder().setAudioAttributes(attributes())
                    .setAudioFormat(new AudioFormat.Builder().setSampleRate(audio.rate).setChannelMask(mask).setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
                    .setTransferMode(AudioTrack.MODE_STATIC).setBufferSizeInBytes(Math.max(data.length,minimum)).build();
                if(track.write(data,0,data.length,AudioTrack.WRITE_BLOCKING)!=data.length)throw new IOException("Audio buffer could not be loaded");
                if(track.setLoopPoints(0,audio.frames(),-1)!=AudioTrack.SUCCESS)throw new IOException("The device rejected the loop buffer");
            }
            track.play();playing=true;resumeAfterFocus=false;status="Playing · continuous loop";publish();
        } catch(Exception error){releaseTrack();playing=false;if(focusHeld)manager.abandonAudioFocusRequest(focus);focusHeld=false;
            status="Playback failed: "+error.getMessage();stopForeground(STOP_FOREGROUND_REMOVE);foreground=false;publish();}
    }
    private void pauseNow(boolean user) {
        if(track!=null&&playing)track.pause();playing=false;
        if(user){resumeAfterFocus=false;if(focusHeld)manager.abandonAudioFocusRequest(focus);focusHeld=false;}
        if(audio!=null)status="Paused";publish();
    }
    private void releaseTrack(){if(track!=null){track.release();track=null;}}
    private void publish(){if(foreground)((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).notify(1,notification());if(listener!=null)listener.changed();}
    private void foreground() {
        foreground=true;
        if(Build.VERSION.SDK_INT>=29)startForeground(1,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK);
        else startForeground(1,notification());
    }
    private Notification notification() {
        PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent toggle=PendingIntent.getService(this,1,new Intent(this,LoopService.class).setAction(TOGGLE),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop=PendingIntent.getService(this,2,new Intent(this,LoopService.class).setAction(STOP),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,CHANNEL).setSmallIcon(R.drawable.ic_beacon).setContentTitle("Beacon Loop")
            .setContentText(title+" · "+(playing?"Playing":"Paused")).setContentIntent(open).setOngoing(playing).setOnlyAlertOnce(true)
            .addAction(new Notification.Action.Builder(null,playing?"Pause":"Play",toggle).build())
            .addAction(new Notification.Action.Builder(null,"Stop",stop).build()).build();
    }
    @Override public void onDestroy(){listener=null;foreground=false;stopForeground(STOP_FOREGROUND_REMOVE);pauseNow(true);releaseTrack();worker.shutdownNow();super.onDestroy();}
}
