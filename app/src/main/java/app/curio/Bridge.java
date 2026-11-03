package app.curio;

import android.Manifest;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import org.json.JSONObject;

/** Methods the Curio page can call as window.CurioAndroid. */
public class Bridge {
    private final MainActivity activity;
    private final Context ctx;
    private final WebView web;
    private final Handler ui = new Handler(Looper.getMainLooper());

    Bridge(MainActivity activity, WebView web) {
        this.activity = activity;
        this.ctx = activity.getApplicationContext();
        this.web = web;
    }

    private SharedPreferences sp() {
        return ctx.getSharedPreferences(Reminders.PREFS, Context.MODE_PRIVATE);
    }

    @JavascriptInterface
    public String getPrefs() {
        return sp().getString("page_prefs", "");
    }

    @JavascriptInterface
    public void setPrefs(String json) {
        sp().edit().putString("page_prefs", json).apply();
    }

    @JavascriptInterface
    public String cachedFeed() {
        return Feed.readCache(ctx);
    }

    @JavascriptInterface
    public String feedBase() {
        return Feed.BASE;
    }

    @JavascriptInterface
    public void fetchFeed() {
        new Thread(() -> {
            String body = Feed.fetch(ctx, 8000, 20000);
            ui.post(() -> {
                if (body != null) {
                    web.evaluateJavascript("window.__feed(" + JSONObject.quote(body) + ", true)", null);
                } else {
                    web.evaluateJavascript("window.__feedFail && window.__feedFail()", null);
                }
            });
        }).start();
    }

    @JavascriptInterface
    public String getReminder() {
        try {
            JSONObject o = new JSONObject();
            o.put("enabled", Reminders.enabled(ctx));
            o.put("hour", Reminders.hour(ctx));
            o.put("minute", Reminders.minute(ctx));
            o.put("allowed", notificationsAllowed());
            return o.toString();
        } catch (Exception e) {
            return "{}";
        }
    }

    @JavascriptInterface
    public void setReminder(boolean enabled, int hour, int minute) {
        Reminders.set(ctx, enabled, hour, minute);
        if (enabled) ui.post(activity::askForNotifications);
    }

    @JavascriptInterface
    public boolean notificationsAllowed() {
        return Build.VERSION.SDK_INT < 33
                || ctx.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    @JavascriptInterface
    public void testNotification() {
        new Thread(() -> {
            String body = Feed.readCache(ctx);
            Reminders.notify(ctx, Feed.summary(body));
        }).start();
    }

    @JavascriptInterface
    public void copy(String text) {
        ClipboardManager cm = (ClipboardManager) ctx.getSystemService(Context.CLIPBOARD_SERVICE);
        if (cm != null) cm.setPrimaryClip(ClipData.newPlainText("Curio", text));
    }
}
