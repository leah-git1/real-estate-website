// ChatController.cs

using Microsoft.AspNetCore.Mvc;
using Services;
using DTOs;

[ApiController]

[Route("api/[controller]")]

public class ChatController : ControllerBase

{

    private readonly HttpClient _http;
    private readonly IProductService _productService;
    private readonly IUsersServices _usersService;

    public ChatController(IHttpClientFactory factory, IProductService productService, IUsersServices usersService)
    {
        _http = factory.CreateClient();
        _productService = productService;
        _usersService = usersService;
    }


    [HttpPost]
    public async Task<IActionResult> Post([FromBody] ChatRequest req)
    {
        var result = await _productService.GetProducts([], null, null, null, null, null, null, 0, 0);
        var products = result.Data;

        var ownerIds = products.Where(p => p.OwnerId.HasValue).Select(p => p.OwnerId!.Value).Distinct();
        var owners = new Dictionary<int, UserProfileDTO>();
        foreach (var id in ownerIds)
        {
            try { owners[id] = await _usersService.GetUserById(id); } catch { }
        }

        var productList = products.Select(p => new
        {
            p.ProductId,
            p.Title,
            p.Price,
            p.City,
            p.Rooms,
            p.Beds,
            p.TransactionType,
            p.CategoryCategoryName,
            p.IsAvailable,
            Link = $"http://localhost:4200/product-details/{p.ProductId}",
            Owner = p.OwnerId.HasValue && owners.TryGetValue(p.OwnerId.Value, out var o)
                ? new { o.FullName, o.Phone, o.Address }
                : null
        }).ToList();


        var payload = new
        {

            message = req.Message,

            history = req.History,

            products = productList // real data from DB

        };


        var res = await _http.PostAsJsonAsync(

        "http://localhost:8001/chat", payload);

        var data = await res.Content.ReadFromJsonAsync<ChatResponse>();

        return Ok(data);

    }

}


public record ChatRequest(

string Message,

List<HistoryItem> History,

List<object> Products); // empty for now


public record HistoryItem(string Role, string Content);

public record ChatResponse(string Reply);