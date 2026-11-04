# syntax=docker/dockerfile:1

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY Chatbot.sln ./
COPY Chatbot.Api/Chatbot.Api.csproj Chatbot.Api/
COPY Chatbot.Api.Tests/Chatbot.Api.Tests.csproj Chatbot.Api.Tests/
RUN dotnet restore Chatbot.Api/Chatbot.Api.csproj

COPY . .
RUN dotnet publish Chatbot.Api/Chatbot.Api.csproj \
    --configuration Release \
    --output /app/publish \
    /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app

ENV ASPNETCORE_URLS=http://+:8080 \
    ASPNETCORE_ENVIRONMENT=Production \
    ConnectionStrings__Chatbot="Data Source=/app/data/chatbot.db"

EXPOSE 8080

RUN mkdir -p /app/data && chown app:app /app/data
USER app

COPY --from=build --chown=app:app /app/publish .

VOLUME ["/app/data"]

ENTRYPOINT ["dotnet", "Chatbot.Api.dll"]
