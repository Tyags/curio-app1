package app.curio;

import android.Manifest;
import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;

import java.util.Calendar;

/** Daily morning reminder: stored time, alarm scheduling and the notification itself. */
final class Reminders {
    static final String PREFS = "curio";
    static final String ACTION = "app.curio.REMIND";
    private static final String CHANNEL = "morning";

    private Reminders() { }

    private static SharedPreferences sp(Context c) {
        return c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    static boolean enabled(Context c) { return sp(c).getBoolean("r_on", true); }
    static int hour(Context c) { return sp(c).getInt("r_h", 7); }
    static int minute(Context c) { return sp(c).getInt("r_m", 30); }

    static void set(Context c, boolean on, int h, int m) {
        sp(c).edit().putBoolean("r_on", on).putInt("r_h", h).putInt("r_m", m).apply();
        schedule(c);
    }

    static void schedule(Context c) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        Intent i = new Intent(c, ReminderReceiver.class).setAction(ACTION);
        PendingIntent pi = PendingIntent.getBroadcast(c, 0, i,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        am.cancel(pi);
        if (!enabled(c)) return;

        Calendar next = Calendar.getInstance();
        next.set(Calendar.HOUR_OF_DAY, hour(c));
        next.set(Calendar.MINUTE, minute(c));
        next.set(Calendar.SECOND, 0);
        next.set(Calendar.MILLISECOND, 0);
        if (next.getTimeInMillis() <= System.currentTimeMillis() + 30_000) next.add(Calendar.DAY_OF_YEAR, 1);
        am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, next.getTimeInMillis(), pi);
    }

    static void ensureChannel(Context c) {
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        if (nm.getNotificationChannel(CHANNEL) != null) return;
        NotificationChannel ch = new NotificationChannel(CHANNEL, "Morning reminder",
                NotificationManager.IMPORTANCE_DEFAULT);
        ch.setDescription("A daily nudge when the new batch of cards is ready");
        nm.createNotificationChannel(ch);
    }

    static void notify(Context c, String[] s) {
        if (Build.VERSION.SDK_INT >= 33
                && c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            return;
        }
        ensureChannel(c);
        Intent open = new Intent(c, MainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi = PendingIntent.getActivity(c, 1, open,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification n = new Notification.Builder(c, CHANNEL)
                .setSmallIcon(R.drawable.ic_notif)
                .setColor(0xFF9DB8FF)
                .setContentTitle(s[0])
                .setContentText(s[1])
                .setStyle(new Notification.BigTextStyle().bigText(s[1]))
                .setContentIntent(pi)
                .setAutoCancel(true)
                .build();
        c.getSystemService(NotificationManager.class).notify(7, n);
    }
}
