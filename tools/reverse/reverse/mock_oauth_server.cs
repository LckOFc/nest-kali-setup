using System;
using System.Net;
using System.Text;
using Newtonsoft.Json;

public class MockOAuthServer {
    private HttpListener listener;
    private string accessToken = "mock_access_token_12345";
    
    public void Start(int port = 9999) {
        listener = new HttpListener();
        listener.Prefixes.Add($"http://localhost:{port}/");
        listener.Start();
        Console.WriteLine($"Mock OAuth Server running on port {port}");
        Console.WriteLine($"Access Token: {accessToken}");
        
        while (true) {
            var context = listener.GetContext();
            Task.Run(() => HandleRequest(context));
        }
    }
    
    private void HandleRequest(HttpListenerContext context) {
        var request = context.Request;
        var response = context.Response;
        
        Console.WriteLine($"Request: {request.Url}");
        
        if (request.Url.PathAndQuery.Contains("/token")) {
            // Mock token response
            var tokenResponse = JsonConvert.SerializeObject(new {
                access_token = accessToken,
                token_type = "Bearer",
                expires_in = 3600
            });
            byte[] buffer = Encoding.UTF8.GetBytes(tokenResponse);
            response.ContentType = "application/json";
            response.ContentLength64 = buffer.Length;
            response.OutputStream.Write(buffer, 0, buffer.Length);
        } else if (request.Url.PathAndQuery.Contains("/authorize")) {
            // Mock authorization - redirect with code
            response.Redirect("http://localhost:9999/callback?code=mock_auth_code");
        } else if (request.Url.PathAndQuery.Contains("/callback")) {
            // Mock callback - show success
            var html = "<html><body><h1>Authentication Successful!</h1><p>You can close this window.</p></body></html>";
            byte[] buffer = Encoding.UTF8.GetBytes(html);
            response.ContentType = "text/html";
            response.ContentLength64 = buffer.Length;
            response.OutputStream.Write(buffer, 0, buffer.Length);
        } else {
            // Default response
            var data = Encoding.UTF8.GetBytes("{\"status\": \"ok\"}");
            response.ContentType = "application/json";
            response.ContentLength64 = data.Length;
            response.OutputStream.Write(data, 0, data.Length);
        }
        
        response.Close();
    }
}

public class Program {
    public static void Main(string[] args) {
        var server = new MockOAuthServer();
        server.Start(9999);
    }
}
