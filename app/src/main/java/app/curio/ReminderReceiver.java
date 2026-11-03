package app.curio;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Fires the morning notification, and re-arms the alarm after reboots and updates. */
public class ReminderReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        final Context app = context.getApplicationContext();
        if (!Reminders.ACTION.equals(intent.getAction())) {
            Reminders.schedule(app);
            return;
        }
        final PendingResult pending = goAsync();
        new Thread(() -> {
            try {
                String body = Feed.fetch(app, 3000, 5000);
                if (body == null) body = Feed.readCache(app);
                Reminders.notify(app, Feed.summary(body));
            } finally {
                Reminders.schedule(app);
                pending.finish();
            }
        }).start();
    }
}
