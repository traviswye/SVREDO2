using Hangfire;
using Microsoft.EntityFrameworkCore;
using SharpVizAPI.Models; // Directly import the GamePreview class
using SharpVizAPI.Data; // Directly import the GamePreview class
using SharpVizAPI.Services;
using SharpVizApi.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.

builder.Services.AddControllers();

// Add CORS policy
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowLocalhostReactApp", builder =>
    {
        builder.WithOrigins("http://localhost:3000") // Allow requests from React app
               .AllowAnyHeader() // Allow any headers
               .AllowAnyMethod(); // Allow any HTTP method

        builder.WithOrigins("http://localhost:3001") // Allow requests from React app
       .AllowAnyHeader() // Allow any headers
       .AllowAnyMethod(); // Allow any HTTP method
    });
});

// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddHttpClient();
builder.Services.AddHttpClient<EvaluationService>();
builder.Services.AddDbContext<NrfidbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

builder.Services.AddHangfire(config =>
    config.UseSqlServerStorage(builder.Configuration.GetConnectionString("DefaultConnection")));

builder.Services.AddHangfireServer();
builder.Services.AddScoped<PropsService>();
builder.Services.AddScoped<WeatherService>();
builder.Services.AddScoped<LineupService>();
builder.Services.AddScoped<EvaluationService>();
builder.Services.AddScoped<NormalizationService>();
builder.Services.AddScoped<PlayerIDMappingService>();
builder.Services.AddScoped<BlendingService>();
builder.Services.AddScoped<IClassificationService, ClassificationService>();
builder.Services.AddScoped<BJmodelingService>();
builder.Services.AddScoped<IDfsOptimizationService, DfsOptimizationService>();
builder.Services.AddScoped<IMLBStrategyService, MLBStrategyService>();
builder.Services.AddScoped<BullpenAnalysisService>(); 

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
    app.UseDeveloperExceptionPage();
}

// Add CORS middleware
app.UseCors("AllowLocalhostReactApp");

app.UseHangfireServer();

//app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();
