using Chatbot.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace Chatbot.Api.Data;

public class ChatbotDbContext(DbContextOptions<ChatbotDbContext> options) : DbContext(options)
{
    public DbSet<Conversation> Conversations => Set<Conversation>();

    public DbSet<Message> Messages => Set<Message>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Conversation>(entity =>
        {
            entity.HasKey(c => c.Id);
            entity.Property(c => c.Title).HasMaxLength(200).IsRequired();

            entity.HasMany(c => c.Messages)
                .WithOne(m => m.Conversation)
                .HasForeignKey(m => m.ConversationId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<Message>(entity =>
        {
            entity.HasKey(m => m.Id);
            entity.Property(m => m.Role).HasMaxLength(32).IsRequired();
            entity.Property(m => m.Content).IsRequired();

            entity.HasIndex(m => new { m.ConversationId, m.CreatedAt });
        });
    }
}
