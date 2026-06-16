import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpRequest, HttpEventType } from '@angular/common/http';
import { Observable, map, filter } from 'rxjs';
import { UserService } from './user-service';

export interface PriceRange { min: number; max: number; }

export interface ValuationDetails {
  kitchen:     string;
  lighting:    string;
  renovations: string;
  flooring:    string;
  overall:     string;
}

export interface ValuationResponse {
  isGuest:     boolean;
  valuation?:  number;
  confidence?: number;
  priceRange?: PriceRange;
  details?:    ValuationDetails;
}

@Injectable({ providedIn: 'root' })
export class ValuationService {
  private readonly apiUrl = 'https://localhost:44305/api/valuation/upload';

  constructor(private http: HttpClient, private userService: UserService) {}

  /**
   * Sends property metadata + JPEG image files as multipart/form-data.
   * This is the only method the component should call.
   * Files must be image/jpeg — video blobs are rejected by the backend.
   */
  analyzeMultipart(
    files:   File[],
    address: string,
    city:    string,
    rooms:   number,
    sqm:     number
  ): Observable<ValuationResponse> {
    const user = this.userService.getCurrentUser();

    const form = new FormData();
    form.append('address', address);
    form.append('city',    city);
    form.append('rooms',   rooms.toString());
    form.append('sqm',     sqm.toString());

    // Append each JPEG — backend reads these as IFormFile[]
    files.forEach((f, i) => form.append(`images`, f, `image_${i}.jpg`));

    const headers = new HttpHeaders({ 'UserId': user?.userId?.toString() ?? '0' });

    // Use HttpRequest so we can track upload progress
    const req = new HttpRequest('POST', this.apiUrl, form, {
      headers,
      reportProgress: true
    });

    return this.http.request<ValuationResponse>(req).pipe(
      filter(e => e.type === HttpEventType.Response),
      map(e => (e as any).body as ValuationResponse)
    );
  }
}
