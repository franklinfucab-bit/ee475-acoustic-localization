package org.ee475.beaconloop;

import android.Manifest;
import android.app.Activity;
import android.content.*;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.media.AudioManager;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import android.view.*;
import android.widget.*;

public final class MainActivity extends Activity {
    private LoopService service;private boolean bound,updating;
    private TextView file,status,details;private Button tone,gap,choose,play;private CheckBox normalize;
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private final ServiceConnection connection=new ServiceConnection(){
        @Override public void onServiceConnected(ComponentName name,IBinder binder){
            service=((LoopService.LocalBinder)binder).service();bound=true;service.listener=()->refresh();
            if(!service.ready()&&!service.loading) {
                boolean cached=getSharedPreferences("player",0).getBoolean("has_cached",false);
                command(LoopService.LOAD,cached?"cache":null,getSharedPreferences("player",0).getString("name","Default 20 kHz beacon"));
            }
            refresh();
        }
        @Override public void onServiceDisconnected(ComponentName name){bound=false;service=null;refresh();}
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);setVolumeControlStream(AudioManager.STREAM_MUSIC);
        LinearLayout layout=new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);layout.setBackgroundColor(Color.rgb(16,35,48));
        layout.setPadding(dp(24),dp(24),dp(24),dp(24));
        layout.setOnApplyWindowInsetsListener((view,insets)->{view.setPadding(dp(24),dp(24)+insets.getSystemWindowInsetTop(),dp(24),dp(24)+insets.getSystemWindowInsetBottom());return insets;});
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.addView(layout);setContentView(scroll);
        TextView heading=text("Beacon Loop",30);heading.setTypeface(null,Typeface.BOLD);layout.addView(heading);
        TextView sub=text("Local audio. Built-in beacons or one file. Continuous playback.",15);layout.addView(sub);space(layout,30);
        file=text("Default 20 kHz beacon",20);file.setTypeface(null,Typeface.BOLD);layout.addView(file);space(layout,10);
        details=text("Loading…",14);layout.addView(details);space(layout,24);
        tone=button("19-21 kHz beacon",false);layout.addView(tone,new LinearLayout.LayoutParams(-1,dp(56)));space(layout,12);
        gap=button("Gap test 18-22 kHz",false);layout.addView(gap,new LinearLayout.LayoutParams(-1,dp(56)));space(layout,12);
        choose=button("Choose audio file",false);layout.addView(choose,new LinearLayout.LayoutParams(-1,dp(56)));space(layout,12);
        play=button("Play loop",true);layout.addView(play,new LinearLayout.LayoutParams(-1,dp(60)));space(layout,20);
        normalize=new CheckBox(this);normalize.setText("Gentle level normalization (optional)");normalize.setTextColor(Color.rgb(210,229,235));normalize.setTextSize(14);layout.addView(normalize);
        layout.addView(text("Off by default. Same frequency, timing and channels.\nGain boost is limited to +3 dB; original files stay unchanged.",13));space(layout,24);
        status=text("Ready",16);status.setTextColor(Color.rgb(101,222,196));layout.addView(status);
        LinearLayout.LayoutParams filler=new LinearLayout.LayoutParams(1,0,1);layout.addView(new Space(this),filler);
        layout.addView(text("Use the phone's media volume keys.\nUse the same beacon file/reference in the PC receiver.\nNo network or microphone access.",13));
        tone.setOnClickListener(view->command(LoopService.LOAD,"asset:default-beacon.wav","19-21 kHz beacon"));
        gap.setOnClickListener(view->command(LoopService.LOAD,"asset:gap-beacon.wav","Gap test 18-22 kHz"));
        choose.setOnClickListener(view->{Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("audio/*").addCategory(Intent.CATEGORY_OPENABLE)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION).putExtra(Intent.EXTRA_LOCAL_ONLY,true);startActivityForResult(intent,10);});
        play.setOnClickListener(view->command(LoopService.TOGGLE,null,null));
        normalize.setOnCheckedChangeListener((view,value)->{if(!updating&&service!=null)service.setNormalize(value);});
        if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},20);
    }
    private TextView text(String value,int size){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(Color.rgb(190,211,221));t.setLineSpacing(dp(3),1);return t;}
    private Button button(String value,boolean accent){Button b=new Button(this);b.setText(value);b.setAllCaps(false);b.setTextSize(17);b.setTextColor(Color.WHITE);
        GradientDrawable bg=new GradientDrawable();bg.setCornerRadius(dp(12));bg.setColor(accent?Color.rgb(0,127,115):Color.rgb(38,65,80));b.setBackground(bg);return b;}
    private void space(LinearLayout layout,int size){layout.addView(new Space(this),new LinearLayout.LayoutParams(1,dp(size)));}
    private void command(String action,String uri,String name){Intent intent=new Intent(this,LoopService.class).setAction(action);
        if(uri!=null)intent.putExtra("uri",uri);if(name!=null)intent.putExtra("name",name);
        if(LoopService.STOP.equals(action))startService(intent);else startForegroundService(intent);}
    private void refresh(){if(service==null)return;updating=true;file.setText(service.title);details.setText(service.details());status.setText(service.status);
        play.setText(service.playing?"Pause":"Play loop");play.setEnabled(service.ready()&&!service.loading);
        boolean idle=!service.loading;choose.setEnabled(idle);tone.setEnabled(idle);gap.setEnabled(idle);
        normalize.setChecked(service.normalize);normalize.setEnabled(!service.loading&&!service.playing);updating=false;}
    @Override protected void onStart(){super.onStart();bindService(new Intent(this,LoopService.class),connection,BIND_AUTO_CREATE);}
    @Override protected void onStop(){if(bound){service.listener=null;unbindService(connection);bound=false;service=null;}super.onStop();}
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);
        if(request!=10||result!=RESULT_OK||data==null||data.getData()==null)return;Uri uri=data.getData();
        try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(SecurityException ignored){}
        String name="Selected audio";try(Cursor cursor=getContentResolver().query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)){if(cursor!=null&&cursor.moveToFirst())name=cursor.getString(0);}catch(Exception ignored){}
        command(LoopService.LOAD,uri.toString(),name);
    }
}
