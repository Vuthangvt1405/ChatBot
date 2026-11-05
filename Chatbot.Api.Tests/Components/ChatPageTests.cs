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

    // ---------- US-4 Show that the assistant is working ----------
    // Plan: docs/features/plans/US-4-loading-indicator-plan.md §7
    // Baseline: render, type "Hello", submit with the reply unresolved (request in flight).

    private (IRenderedComponent<Chat> Page, TaskCompletionSource<string> Reply, Task Submit) StartPending(string text = "Hello")
    {
        var reply = new TaskCompletionSource<string>();
        _chat.Pending = reply.Task;
        var page = Render<Chat>();
        page.Find("#chat-input").Input(text);
        var submit = page.Find("#chat-form").SubmitAsync();
        return (page, reply, submit);
    }

    // Group 1 — indicator while waiting (AC1, AC6)

    [Fact]
    public async Task US4_AC1_WhilePending_TypingIndicatorShown()
    {
        var (page, reply, submit) = StartPending();

        var indicator = page.Find("#typing-indicator");
        Assert.Equal("Assistant is typing", indicator.TextContent.Trim());
        Assert.Equal("status", indicator.GetAttribute("role"));
        Assert.Equal([("message user", "You", "Hello")], Messages(page));

        reply.SetResult("Hi");
        await submit;
    }

    [Fact]
    public void US4_AC1_Contrast_FreshPage_NoIndicator()
    {
        var page = Render<Chat>();

        Assert.Empty(page.FindAll("#typing-indicator"));
        Assert.Empty(_chat.Requests);
    }

    [Fact]
    public async Task US4_AC1_Contrast_BlockedSend_NoIndicator()
    {
        var page = Render<Chat>();

        await SendAsync(page, "   ");

        Assert.Empty(page.FindAll("#typing-indicator"));
        Assert.Empty(_chat.Requests);
    }

    [Fact]
    public async Task US4_AC1_Contrast_IndicatorIsNotAMessage()
    {
        var (page, reply, submit) = StartPending();

        Assert.Single(page.FindAll("#messages li"));

        reply.SetResult("Hi");
        await submit;
    }

    // Group 2 — no double send (AC2)

    [Fact]
    public async Task US4_AC2_WhilePending_SendDisabled()
    {
        var (page, reply, submit) = StartPending();

        Assert.True(SendDisabled(page));

        reply.SetResult("Hi");
        await submit;
    }

    [Fact]
    public async Task US4_AC2_WhilePending_Enter_DoesNotSendAgain()
    {
        var (page, reply, submit) = StartPending();

        await page.Find("#chat-input").KeyDownAsync(new KeyboardEventArgs { Key = "Enter" });

        Assert.Single(_chat.Requests);
        Assert.Single(page.FindAll("#messages li.user"));
        reply.SetResult("Hi");
        await submit;
    }

    [Fact]
    public async Task US4_AC2_WhilePending_Submit_DoesNotSendAgain()
    {
        var (page, reply, submit) = StartPending();

        await page.Find("#chat-form").SubmitAsync();

        Assert.Single(_chat.Requests);
        reply.SetResult("Hi");
        await submit;
    }

    [Fact]
    public async Task US4_AC2_WhilePending_NewValidText_StillDisabled()
    {
        var (page, reply, submit) = StartPending();

        await page.Find("#chat-input").InputAsync(new() { Value = "Next" });

        Assert.True(SendDisabled(page));
        reply.SetResult("Hi");
        await submit;
    }

    // Group 3 — indicator clears when done (AC3)

    [Fact]
    public async Task US4_AC3_OnSuccess_IndicatorRemoved_SendReenabledWhenValid()
    {
        var (page, reply, submit) = StartPending();

        reply.SetResult("Hi");
        await submit;
        await page.Find("#chat-input").InputAsync(new() { Value = "Next" });

        Assert.Empty(page.FindAll("#typing-indicator"));
        Assert.False(SendDisabled(page));
    }

    [Fact]
    public async Task US4_AC3_OnSuccess_EmptyInput_SendStaysDisabled()
    {
        var (page, reply, submit) = StartPending();

        reply.SetResult("Hi");
        await submit;

        Assert.Empty(page.FindAll("#typing-indicator"));
        Assert.True(SendDisabled(page));
    }

    [Fact]
    public async Task US4_AC3_OnProviderError_IndicatorRemoved_SendReenabled()
    {
        var (page, reply, submit) = StartPending();

        reply.SetException(new ChatProviderException("boom"));
        await submit;

        page.WaitForAssertion(() => Assert.Empty(page.FindAll("#typing-indicator")));
        Assert.False(SendDisabled(page));
        Assert.Equal("Hello", page.Find("#chat-input").GetAttribute("value"));
        Assert.Empty(page.FindAll("#messages li.assistant"));
    }

    [Fact]
    public async Task US4_AC3_OnTimeout_IndicatorRemoved()
    {
        var (page, reply, submit) = StartPending();

        reply.SetException(new TaskCanceledException());
        await submit;

        page.WaitForAssertion(() => Assert.Empty(page.FindAll("#typing-indicator")));
        Assert.False(SendDisabled(page));
        Assert.Empty(page.FindAll("#messages li.assistant"));
    }

    [Fact]
    public async Task US4_AC3_AfterFailure_CanSendAgain()
    {
        var (page, reply, submit) = StartPending();
        reply.SetException(new ChatProviderException("boom"));
        await submit;

        _chat.Pending = null;
        _chat.Replies.Enqueue("Hi");
        await page.Find("#chat-form").SubmitAsync();

        Assert.Equal(2, _chat.Requests.Count);
        Assert.Single(page.FindAll("#messages li.assistant"));
    }

    // Group 4 — typing while waiting (AC4, AC7)

    [Fact]
    public async Task US4_AC4_WhilePending_InputEditable()
    {
        var (page, reply, submit) = StartPending();

        var input = page.Find("#chat-input");
        Assert.False(input.HasAttribute("disabled"));
        Assert.False(input.HasAttribute("readonly"));
        await input.InputAsync(new() { Value = "Next" });
        Assert.Equal("Next", page.Find("#chat-input").GetAttribute("value"));

        reply.SetResult("Hi");
        await submit;
    }

    [Fact]
    public async Task US4_AC7_DraftTypedWhilePending_KeptAfterReply()
    {
        var (page, reply, submit) = StartPending();
        await page.Find("#chat-input").InputAsync(new() { Value = "Next" });

        reply.SetResult("Hi");
        await submit;

        Assert.Equal("Next", page.Find("#chat-input").GetAttribute("value"));
    }

    [Fact]
    public async Task US4_AC7_Contrast_UnchangedText_ClearedAfterReply()
    {
        var (page, reply, submit) = StartPending();

        reply.SetResult("Hi");
        await submit;

        Assert.Equal("", page.Find("#chat-input").GetAttribute("value") ?? "");
    }

    // Group S1 — server-side guard (AC5, SEC1)

    [Fact]
    public async Task US4_AC5_ForcedSubmitWhilePending_SingleRequest()
    {
        var reply = new TaskCompletionSource<string>();
        _chat.Pending = reply.Task;
        var page = Render<Chat>();
        page.Find("#chat-input").Input("Hello");
        var form = page.Find("#chat-form");

        var first = form.SubmitAsync();
        var second = form.SubmitAsync();

        Assert.Single(_chat.Requests);
        Assert.Single(page.FindAll("#messages li.user"));
        reply.SetResult("Hi");
        await Task.WhenAll(first, second);
    }

    // Group S2 — no leakage on failure (SEC3)

    [Fact]
    public async Task US4_SEC3_OnError_NoExceptionTextShown()
    {
        var (page, reply, submit) = StartPending();

        reply.SetException(new ChatProviderException("secret-detail"));
        await submit;

        page.WaitForAssertion(() => Assert.Empty(page.FindAll("#typing-indicator")));
        Assert.DoesNotContain("secret-detail", page.Markup);
    }


    // ---------- US-5 Keep the conversation after reloading ----------
    // Plan: docs/features/plans/US-5-restore-after-reload-plan.md §7

    private static readonly Guid SavedA = Guid.Parse("3f2b8c1e-6a4d-4e0f-9b7a-2c5d1e8f4a90");

    private void SavedId(string? value) => JSInterop.Setup<string?>("chatStore.get").SetResult(value);

    private static ConversationDto Convo(Guid id, params (string Role, string Text)[] messages) =>
        new(id, "title", DateTime.UtcNow,
            messages.Select((m, i) => new MessageDto(Guid.NewGuid(), m.Role, m.Text, DateTime.UtcNow.AddSeconds(i))).ToList());

    private IRenderedComponent<Chat> RenderRestored()
    {
        SavedId(SavedA.ToString());
        _chat.Conversations[SavedA] = Convo(SavedA,
            ("user", "Hi"), ("assistant", "Hello!"), ("user", "How are you?"), ("assistant", "Fine."));
        var page = Render<Chat>();
        page.WaitForAssertion(() => Assert.Equal(4, Messages(page).Count));
        return page;
    }

    private int Calls(string identifier) =>
        JSInterop.Invocations.Count(i => i.Identifier == identifier);

    // Group 1 — id is saved (AC1, BR-1)

    [Fact]
    public async Task US5_AC1_AfterReply_IdIsSaved()
    {
        var id = Guid.NewGuid();
        _chat.Replies.Enqueue("Hi");
        _chat.ConversationIds.Enqueue(id);
        var page = Render<Chat>();

        await SendAsync(page, "Hello");

        var set = Assert.Single(JSInterop.Invocations["chatStore.set"]);
        Assert.Equal(id.ToString(), set.Arguments.Single());
    }

    [Fact]
    public async Task US5_AC1_FollowUp_SavesLatestId()
    {
        var b = Guid.NewGuid();
        _chat.Replies.Enqueue("Hi");
        _chat.Replies.Enqueue("Again");
        _chat.ConversationIds.Enqueue(Guid.NewGuid());
        _chat.ConversationIds.Enqueue(b);
        var page = Render<Chat>();

        await SendAsync(page, "Hello");
        await SendAsync(page, "More");

        Assert.Equal(b.ToString(), JSInterop.Invocations["chatStore.set"][^1].Arguments.Single());
    }

    [Fact]
    public async Task US5_AC1_Contrast_FailedSend_NothingSaved()
    {
        _chat.Pending = Task.FromException<string>(new ChatProviderException("boom"));
        var page = Render<Chat>();

        await SendAsync(page, "Hello");

        Assert.Equal(0, Calls("chatStore.set"));
    }

    [Fact]
    public void US5_AC1_Contrast_FreshPage_NothingSaved()
    {
        Render<Chat>();

        Assert.Equal(0, Calls("chatStore.set"));
    }

    [Fact]
    public async Task US5_BR1_OnlyIdIsStored()
    {
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();

        await SendAsync(page, "Hello");

        var args = Assert.Single(JSInterop.Invocations["chatStore.set"]).Arguments;
        var only = Assert.Single(args);
        Assert.True(Guid.TryParse(only as string, out _));
    }

    // Group 2 — history reloads (AC2, AC7)

    [Fact]
    public void US5_AC2_SavedId_ShowsHistoryInOrderWithLabels()
    {
        var page = RenderRestored();

        Assert.Equal(
            [
                ("message user", "You", "Hi"),
                ("message assistant", "Assistant", "Hello!"),
                ("message user", "You", "How are you?"),
                ("message assistant", "Assistant", "Fine."),
            ],
            Messages(page));
        Assert.Equal([SavedA], _chat.GetRequests);
    }

    [Fact]
    public void US5_AC2_RestoredHistory_ScrollsToLatest()
    {
        var page = RenderRestored();

        page.WaitForAssertion(() => Assert.Equal(1, Calls("chatScroll.toBottom")));
    }

    [Fact]
    public void US5_AC2_Contrast_NoSavedId_NoFetch()
    {
        SavedId(null);

        var page = Render<Chat>();

        Assert.Empty(_chat.GetRequests);
        Assert.NotNull(page.Find(".empty"));
    }

    [Fact]
    public void US5_AC7_InvalidSavedId_NoFetch_Cleared()
    {
        SavedId("abc");

        var page = Render<Chat>();

        page.WaitForAssertion(() => Assert.Equal(1, Calls("chatStore.clear")));
        Assert.Empty(_chat.GetRequests);
        Assert.Empty(Messages(page));
    }

    [Fact]
    public void US5_AC2_Contrast_EmptyHistory_ShowsEmptyState()
    {
        SavedId(SavedA.ToString());
        _chat.Conversations[SavedA] = Convo(SavedA);

        var page = Render<Chat>();

        page.WaitForAssertion(() => Assert.Single(_chat.GetRequests));
        page.WaitForAssertion(() => Assert.NotNull(page.Find(".empty")));
        Assert.Equal(0, Calls("chatStore.clear"));
    }

    // Group 3 — next send continues (AC3)

    [Fact]
    public async Task US5_AC3_AfterRestore_SendUsesSavedId()
    {
        _chat.Replies.Enqueue("Sure");
        var page = RenderRestored();

        await SendAsync(page, "More");

        Assert.Equal(SavedA, _chat.Requests.Single().ConversationId);
    }

    [Fact]
    public async Task US5_AC3_Contrast_NotFound_SendHasNoId()
    {
        SavedId(SavedA.ToString());
        _chat.Replies.Enqueue("Hi");
        var page = Render<Chat>();
        page.WaitForAssertion(() => Assert.Equal(1, Calls("chatStore.clear")));

        await SendAsync(page, "Hello");

        Assert.Null(_chat.Requests.Single().ConversationId);
    }

    // Group 4 — missing conversation (AC4)

    [Fact]
    public void US5_AC4_NotFound_ClearsId_EmptyChat_NoError()
    {
        SavedId(SavedA.ToString());

        var page = Render<Chat>();

        page.WaitForAssertion(() => Assert.Equal(1, Calls("chatStore.clear")));
        Assert.NotNull(page.Find(".empty"));
        Assert.Empty(page.FindAll("#chat-error"));
        Assert.Empty(page.FindAll("#restore-indicator"));
    }

    [Fact]
    public void US5_AC4_Contrast_Found_IdNotCleared()
    {
        RenderRestored();

        Assert.Equal(0, Calls("chatStore.clear"));
    }

    // Group 5 — loading state (AC5)

    private (IRenderedComponent<Chat> Page, TaskCompletionSource<ConversationDto?> Restore) StartRestoring()
    {
        SavedId(SavedA.ToString());
        var restore = new TaskCompletionSource<ConversationDto?>();
        _chat.PendingConversation = restore.Task;
        var page = Render<Chat>();
        page.WaitForAssertion(() => Assert.NotNull(page.Find("#restore-indicator")));
        return (page, restore);
    }

    [Fact]
    public async Task US5_AC5_WhileRestoring_IndicatorShown_SendDisabled()
    {
        var (page, restore) = StartRestoring();
        await page.Find("#chat-input").InputAsync(new() { Value = "Hello" });

        var indicator = page.Find("#restore-indicator");
        Assert.Equal("status", indicator.GetAttribute("role"));
        Assert.Contains("Loading conversation", indicator.TextContent);
        Assert.Empty(page.FindAll(".empty"));
        Assert.True(SendDisabled(page));

        restore.SetResult(Convo(SavedA, ("user", "Hi")));
    }

    [Fact]
    public async Task US5_AC5_AfterRestore_IndicatorCleared_SendEnabled()
    {
        var (page, restore) = StartRestoring();
        await page.Find("#chat-input").InputAsync(new() { Value = "Hello" });

        restore.SetResult(Convo(SavedA, ("user", "Hi"), ("assistant", "Hello!")));

        page.WaitForAssertion(() => Assert.Empty(page.FindAll("#restore-indicator")));
        Assert.False(SendDisabled(page));
    }

    [Fact]
    public async Task US5_AC5_WhileRestoring_EnterAndSubmit_DoNotSend()
    {
        var (page, restore) = StartRestoring();
        await page.Find("#chat-input").InputAsync(new() { Value = "Hello" });

        await page.Find("#chat-input").KeyDownAsync(new KeyboardEventArgs { Key = "Enter", ShiftKey = false });
        await page.Find("#chat-form").SubmitAsync();

        Assert.Empty(_chat.Requests);
        restore.SetResult(null);
    }

    [Fact]
    public void US5_AC5_Contrast_NoSavedId_NoIndicator()
    {
        SavedId(null);

        var page = Render<Chat>();

        Assert.Empty(page.FindAll("#restore-indicator"));
    }

    // Group 6 — restore failure (AC6; decision D2: keep the saved id)

    [Fact]
    public async Task US5_AC6_RestoreThrows_EmptyChat_IndicatorCleared_SendWorks()
    {
        SavedId(SavedA.ToString());
        _chat.ThrowOnGet = true;
        _chat.Replies.Enqueue("Hi");

        var page = Render<Chat>();

        page.WaitForAssertion(() => Assert.Single(_chat.GetRequests));
        page.WaitForAssertion(() => Assert.Empty(page.FindAll("#restore-indicator")));
        Assert.NotNull(page.Find(".empty"));
        Assert.Equal(0, Calls("chatStore.clear"));
        Assert.DoesNotContain("db down", page.Markup);

        await SendAsync(page, "Hello");

        Assert.Equal(SavedA, _chat.Requests.Single().ConversationId);
        Assert.Equal(["Hello", "Hi"], Messages(page).Select(m => m.Text));
    }

    // Group S1 — encoding (SEC1)

    [Fact]
    public void US5_SEC1_RestoredHtml_RenderedAsText()
    {
        SavedId(SavedA.ToString());
        _chat.Conversations[SavedA] = Convo(SavedA, ("user", "Hi"), ("assistant", "<b>x</b>"));

        var page = Render<Chat>();

        page.WaitForAssertion(() => Assert.Equal(2, Messages(page).Count));
        Assert.Equal("<b>x</b>", Messages(page)[1].Text);
        Assert.Empty(page.FindAll("#messages b"));
    }

    private sealed class FakeChatService : IChatService
    {
        public List<ChatRequest> Requests { get; } = [];
        public Queue<string> Replies { get; } = new();
        public Task<string>? Pending { get; set; }
        public Queue<Guid> ConversationIds { get; } = new();

        // US-5 restore setup.
        public Dictionary<Guid, ConversationDto> Conversations { get; } = [];
        public Task<ConversationDto?>? PendingConversation { get; set; }
        public bool ThrowOnGet { get; set; }
        public List<Guid> GetRequests { get; } = [];

        public async Task<ChatResponse> SendMessageAsync(ChatRequest request, CancellationToken cancellationToken)
        {
            Requests.Add(request);
            var reply = Pending is not null ? await Pending : Replies.Dequeue();
            var conversationId = ConversationIds.Count > 0 ? ConversationIds.Dequeue() : request.ConversationId ?? Guid.NewGuid();
            return new ChatResponse(conversationId, Guid.NewGuid(), reply, DateTime.UtcNow);
        }

        public async Task<ConversationDto?> GetConversationAsync(Guid conversationId, CancellationToken cancellationToken)
        {
            GetRequests.Add(conversationId);

            if (ThrowOnGet)
            {
                throw new InvalidOperationException("db down");
            }

            return PendingConversation is not null
                ? await PendingConversation
                : Conversations.GetValueOrDefault(conversationId);
        }
    }
}
