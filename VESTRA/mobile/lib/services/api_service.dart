import '../core/network/api_client.dart';

class ApiService {
  Future<Map<String, dynamic>> getConfig() async {
    final data = await ApiClient.get('/api/config');
    return Map<String, dynamic>.from(data);
  }

  Future<List<dynamic>> getRooms() async {
    final data = await ApiClient.get('/api/rooms');

    if (data is Map && data['rooms'] is List) {
      return List<dynamic>.from(data['rooms']);
    }

    return [];
  }

  Future<Map<String, dynamic>> getDiscover() async {
    final data = await ApiClient.get('/api/discover');
    return Map<String, dynamic>.from(data);
  }

  Future<Map<String, dynamic>> getStore() async {
    final data = await ApiClient.get('/api/store');
    return Map<String, dynamic>.from(data);
  }

  Future<Map<String, dynamic>> getFriends() async {
    final data = await ApiClient.get('/api/friends');
    return Map<String, dynamic>.from(data);
  }

  Future<Map<String, dynamic>> getWallet(int userId) async {
    final data = await ApiClient.get('/api/wallet/$userId');
    return Map<String, dynamic>.from(data);
  }
}
