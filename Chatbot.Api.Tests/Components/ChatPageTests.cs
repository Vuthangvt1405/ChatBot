using Bunit;
using Chatbot.Api.Components.Pages;
using Chatbot.Api.DTOs;
using Chatbot.Api.Services;
using Radzen;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.Extensions.DependencyInjection;

namespace Chatbot.Api.Tests.Components;

/// <summary>US-1 tests for the Blazor chat page.</summary>
public sealed class ChatPageTests : BunitContext
{
    private readonly FakeChatService _chat = new();

    public ChatPageTests()
    {
        Services.AddSingleton<IChatService>(_chat);
        Services.AddRadzenComponents();
        JSInterop.Mode = JSRuntimeMode.Loose;
    }

    private static async Task SendAsync(IRenderedComponent<Chat> page, string text)
    {
        await page.Find("#chat-input").InputAsync(new() { Value = text });
        await page.Find("#chat-form").SubmitAsync();
    }

    private static List<(string Class, string Label, string Text)> Messages(IRenderedComponent<Chat> page) =>
        page.FindAll("#messages li")
            .Select(li => (li.ClassName!, li.QuerySelector(".label")!.TextContent, li.QuerySelector(".text")!.TextContent))
            .ToList();

    [Fact]
    public async Task AC1_Send_ShowsMyMessageThenReply()
    {
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();

        await SendAsync(page, "Hello");

        Assert.Single(_chat.Requests);
        Assert.Equal(["Hello", "Hi"], Messages(page).Select(m => m.Text));
    }

    [Fact]
    public void AC1_Contrast_NothingSent_NoMessagesNoRequest()
    {
        var page = Render<Chat>();

        Assert.Empty(_chat.Requests);
        Assert.Empty(Messages(page));
    }

    [Fact]
    public async Task AC2_Messages_AreLabelledAndInOrder()
    {
        _chat.Replies.Enqueue("Hi");
        _chat.Replies.Enqueue("Fine");
        var page = Render<Chat>();

        await SendAsync(page, "Hello");
        await SendAsync(page, "How are you?");

        Assert.Equal(
            [
                ("message user", "You", "Hello"),
                ("message assistant", "Assistant", "Hi"),
                ("message user", "You", "How are you?"),
                ("message assistant", "Assistant", "Fine"),
            ],
            Messages(page));
    }

    [Fact]
    public async Task AC2_Contrast_ReplyIsNotStyledAsMine()
    {
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();

        await SendAsync(page, "Hello");

        var reply = Messages(page)[1];
        Assert.NotEqual("message user", reply.Class);
        Assert.NotEqual("You", reply.Label);
    }

    [Fact]
    public async Task AC3_Enter_Sends()
    {
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();
        await page.Find("#chat-input").InputAsync(new() { Value = "Hello" });

        await page.Find("#chat-input").KeyDownAsync(new KeyboardEventArgs { Key = "Enter", ShiftKey = false });

        Assert.Single(_chat.Requests);
    }

    [Fact]
    public async Task AC3_Contrast_ShiftEnter_DoesNotSend()
    {
        var page = Render<Chat>();
        await page.Find("#chat-input").InputAsync(new() { Value = "Hello" });

        await page.Find("#chat-input").KeyDownAsync(new KeyboardEventArgs { Key = "Enter", ShiftKey = true });

        Assert.Empty(_chat.Requests);
    }

    [Fact]
    public async Task AC4_AfterReply_InputIsEmptyAndFocused()
    {
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();

        await SendAsync(page, "Hello");

        Assert.Equal("", page.Find("#chat-input").GetAttribute("value") ?? "");
        JSInterop.VerifyFocusAsyncInvoke();
    }

    [Fact]
    public async Task AC4_Contrast_WhileReplyPending_InputIsKept()
    {
        var pending = new TaskCompletionSource<string>();
        _chat.Pending = pending.Task;
        var page = Render<Chat>();

        await page.Find("#chat-input").InputAsync(new() { Value = "Hello" });
        var submit = page.Find("#chat-form").SubmitAsync();

        Assert.Equal("Hello", page.Find("#chat-input").GetAttribute("value"));
        pending.SetResult("Hi");
        await submit;
    }

    [Fact]
    public async Task AC5_Message_IsTrimmed()
    {
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();

        await SendAsync(page, "  Hello  ");

        Assert.Equal("Hello", _chat.Requests.Single().Message);
        Assert.Null(_chat.Requests.Single().ConversationId);
    }

    [Fact]
    public async Task AC5_Contrast_InnerSpacesAreKept()
    {
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();

        await SendAsync(page, "Hello  world");

        Assert.Equal("Hello  world", _chat.Requests.Single().Message);
    }

    // ---------- US-2 Keep chatting in the same conversation ----------

    private static readonly Guid Abc = Guid.Parse("00000000-0000-0000-0000-000000000abc");
    private static readonly Guid Def = Guid.Parse("00000000-0000-0000-0000-000000000def");

    [Fact]
    public async Task US2_AC1_FirstMessage_HasNoConversationId()
    {
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();

        await SendAsync(page, "Hello");

        Assert.Null(_chat.Requests.Single().ConversationId);
    }

    [Fact]
    public async Task US2_AC2_FollowUp_ReusesReturnedConversationId()
    {
        _chat.Replies.Enqueue("Hi");
        _chat.Replies.Enqueue("Fine");
        _chat.ConversationIds.Enqueue(Abc);
        var page = Render<Chat>();

        await SendAsync(page, "Hello");
        await SendAsync(page, "  How are you?  ");

        Assert.Equal(Abc, _chat.Requests[1].ConversationId);
        Assert.Equal("How are you?", _chat.Requests[1].Message);
    }

    [Fact]
    public async Task US2_BR1_UsesIdFromLatestResponse()
    {
        _chat.Replies.Enqueue("1");
        _chat.Replies.Enqueue("2");
        _chat.Replies.Enqueue("3");
        _chat.ConversationIds.Enqueue(Abc);
        _chat.ConversationIds.Enqueue(Def);
        var page = Render<Chat>();

        await SendAsync(page, "a");
        await SendAsync(page, "b");
        await SendAsync(page, "c");

        Assert.Equal(Def, _chat.Requests[2].ConversationId);
    }

    [Fact]
    public async Task US2_AC3_EarlierMessages_StayInOrder_NewPairAtBottom()
    {
        _chat.Replies.Enqueue("1");
        _chat.Replies.Enqueue("2");
        _chat.Replies.Enqueue("3");
        var page = Render<Chat>();

        await SendAsync(page, "a");
        await SendAsync(page, "b");
        await SendAsync(page, "c");

        Assert.Equal(["a", "1", "b", "2", "c", "3"], Messages(page).Select(m => m.Text));
    }

    [Fact]
    public async Task US2_AC4_NewMessages_ScrollToLatest()
    {
        var pending = new TaskCompletionSource<string>();
        _chat.Pending = pending.Task;
        var page = Render<Chat>();

        await page.Find("#chat-input").InputAsync(new() { Value = "Hello" });
        var submit = page.Find("#chat-form").SubmitAsync();

        // My message is shown and scrolled into view before the reply arrives.
        Assert.Single(JSInterop.Invocations["chatScroll.toBottom"]);

        pending.SetResult("Hi");
        await submit;

        page.WaitForAssertion(() => Assert.Equal(2, JSInterop.Invocations["chatScroll.toBottom"].Count));
    }

    [Fact]
    public void US2_AC4_Contrast_NoNewMessages_NoScroll()
    {
        Render<Chat>();

        Assert.Empty(JSInterop.Invocations["chatScroll.toBottom"]);
    }

    // ---------- US-3 Block invalid messages ----------

    private static readonly string Max = new('a', 4000);
    private static readonly string TooLong = new('a', 4001);

    private static Task TypeAsync(IRenderedComponent<Chat> page, string text) =>
        page.Find("#chat-input").InputAsync(new() { Value = text });

    private static bool SendDisabled(IRenderedComponent<Chat> page) =>
        page.Find("button[aria-label=Send]").HasAttribute("disabled");

    private static async Task TrySendAllWaysAsync(IRenderedComponent<Chat> page)
    {
        await page.Find("#chat-input").KeyDownAsync(new KeyboardEventArgs { Key = "Enter" });
        await page.Find("#chat-form").SubmitAsync();
    }

    [Fact]
    public async Task US3_AC1_WhitespaceOnly_SendDisabled()
    {
        var page = Render<Chat>();

        await TypeAsync(page, "   ");

        Assert.True(SendDisabled(page));
    }

    [Fact]
    public async Task US3_AC1_Contrast_Text_SendEnabled()
    {
        var page = Render<Chat>();

        await TypeAsync(page, "Hello");

        Assert.False(SendDisabled(page));
    }

    [Fact]
    public void US3_AC1_FreshPage_SendDisabled()
    {
        var page = Render<Chat>();

        Assert.True(SendDisabled(page));
    }

    [Fact]
    public async Task US3_AC1_WhitespaceOnly_EnterAndSubmit_DoNotSend()
    {
        var page = Render<Chat>();
        await TypeAsync(page, "   ");

        await TrySendAllWaysAsync(page);

        Assert.Empty(_chat.Requests);
        Assert.Empty(Messages(page));
    }

    private const string TooLongError = "Message must be 4000 characters or fewer";

    [Fact]
    public async Task US3_AC2_TooLong_SendDisabled_ErrorShown()
    {
        var page = Render<Chat>();

        await TypeAsync(page, TooLong);

        Assert.True(SendDisabled(page));
        Assert.Equal(TooLongError, page.Find("#chat-error").TextContent.Trim());
        Assert.Empty(page.FindAll(".hint"));
    }

    [Fact]
    public async Task US3_AC2_TooLong_EnterAndSubmit_DoNotSend_TextKept()
    {
        var page = Render<Chat>();
        await TypeAsync(page, TooLong);

        await TrySendAllWaysAsync(page);

        Assert.Empty(_chat.Requests);
        Assert.Empty(Messages(page));
        Assert.Equal(TooLong, page.Find("#chat-input").GetAttribute("value"));
    }

    [Fact]
    public async Task US3_AC2_ShortenedBackToLimit_ErrorClears()
    {
        var page = Render<Chat>();
        await TypeAsync(page, TooLong);

        await TypeAsync(page, Max);

        Assert.Empty(page.FindAll("#chat-error"));
        Assert.Single(page.FindAll(".hint"));
        Assert.False(SendDisabled(page));
    }

    [Fact]
    public async Task US3_AC3_Exactly4000_IsSent()
    {
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();
        await TypeAsync(page, Max);

        Assert.False(SendDisabled(page));
        Assert.Empty(page.FindAll("#chat-error"));

        await page.Find("#chat-form").SubmitAsync();

        Assert.Equal(4000, _chat.Requests.Single().Message.Length);
    }

    [Fact]
    public async Task US3_AC3_4000PlusOuterSpaces_IsSent_Trimmed()
    {
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();

        await SendAsync(page, "  " + Max + "  ");

        Assert.Equal(Max, _chat.Requests.Single().Message);
    }

    [Fact]
    public async Task US3_AC4_Counter_ShowsTrimmedLength()
    {
        var page = Render<Chat>();

        await TypeAsync(page, "  Hi  ");

        var counter = page.Find("#char-count");
        Assert.Equal("2 / 4000", counter.TextContent.Trim());
        Assert.False(counter.ClassList.Contains("over"));
    }

    [Fact]
    public async Task US3_AC4_Contrast_OverLimit_CounterWarns()
    {
        var page = Render<Chat>();

        await TypeAsync(page, TooLong);

        var counter = page.Find("#char-count");
        Assert.Equal("4001 / 4000", counter.TextContent.Trim());
        Assert.True(counter.ClassList.Contains("over"));
    }

    [Fact]
    public async Task US3_AC4_Contrast_EmptyOrWhitespace_NoCounter()
    {
        var page = Render<Chat>();
        Assert.Empty(page.FindAll("#char-count"));

        await TypeAsync(page, "   ");

        Assert.Empty(page.FindAll("#char-count"));
    }

    private sealed class FakeChatService : IChatService
    {
        public List<ChatRequest> Requests { get; } = [];
        public Queue<string> Replies { get; } = new();
        public Task<string>? Pending { get; set; }
        public Queue<Guid> ConversationIds { get; } = new();

        public async Task<ChatResponse> SendMessageAsync(ChatRequest request, CancellationToken cancellationToken)
        {
            Requests.Add(request);
            var reply = Pending is not null ? await Pending : Replies.Dequeue();
            var conversationId = ConversationIds.Count > 0 ? ConversationIds.Dequeue() : request.ConversationId ?? Guid.NewGuid();
            return new ChatResponse(conversationId, Guid.NewGuid(), reply, DateTime.UtcNow);
        }

        public Task<ConversationDto?> GetConversationAsync(Guid conversationId, CancellationToken cancellationToken) =>
            Task.FromResult<ConversationDto?>(null);
    }
}
