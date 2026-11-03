package app.curio;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Downloads and caches the public card feed published by the daily task. */
final class Feed {
    static final String BASE = "https://raw.githubusercontent.com/Tyags/curio-app1/main/feed/";
    private static final String CACHE = "feed.json";

    private Feed() { }

    static String fetch(Context ctx, int connectMs, int readMs) {
        HttpURLConnection con = null;
        try {
            URL url = new URL(BASE + "latest.json?t=" + (System.currentTimeMillis() / 300000));
            con = (HttpURLConnection) url.openConnection();
            con.setConnectTimeout(connectMs);
            con.setReadTimeout(readMs);
            con.setRequestProperty("Accept", "application/json");
            if (con.getResponseCode() != 200) return null;
            String body = read(con.getInputStream());
            new JSONObject(body); // must parse
            try (FileOutputStream out = new FileOutputStream(new File(ctx.getFilesDir(), CACHE))) {
                out.write(body.getBytes(StandardCharsets.UTF_8));
            }
            return body;
        } catch (Exception e) {
            return null;
        } finally {
            if (con != null) con.disconnect();
        }
    }

    static String readCache(Context ctx) {
        File f = new File(ctx.getFilesDir(), CACHE);
        if (!f.exists()) return "";
        try (FileInputStream in = new FileInputStream(f)) {
            return read(in);
        } catch (Exception e) {
            return "";
        }
    }

    private static String read(InputStream in) throws Exception {
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        byte[] chunk = new byte[16384];
        int n;
        while ((n = in.read(chunk)) > 0) buf.write(chunk, 0, n);
        return buf.toString("UTF-8");
    }

    /** Notification title and text for the latest batch. */
    static String[] summary(String body) {
        String today = new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date());
        try {
            JSONArray days = new JSONObject(body).getJSONArray("days");
            if (days.length() > 0) {
                JSONObject d = days.getJSONObject(0);
                JSONArray cards = d.getJSONArray("cards");
                String first = "";
                for (int i = 0; i < cards.length(); i++) {
                    JSONObject c = cards.getJSONObject(i);
                    if ("news".equals(c.optString("kind"))) { first = c.optString("title"); break; }
                }
                if (today.equals(d.optString("date"))) {
                    String text = cards.length() + " new cards today" + (first.isEmpty() ? "" : " · " + first);
                    return new String[]{"Your Curio is ready", text};
                }
            }
        } catch (Exception ignored) { }
        return new String[]{"Five minutes of Curio?", "Your cards are waiting. Pick up where you left off."};
    }
}
