import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormControl, FormGroup, FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { LoadingComponent } from '../loading/loading.component';
import { NavService } from '../../services/nav.service';
import { PageCard } from '../../models/page-card.model';
import { ReactiveFormsModule } from '@angular/forms';
import { PaginationComponent } from "../pagination/pagination.component";
import { ProductComponent } from '../product/product.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, LoadingComponent, ReactiveFormsModule, PaginationComponent, ProductComponent],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  link: string;
  filters: any;
  currentPage: number = 1; // pagination currentPage number
  navId: number;
  limit: number = 10; // limit for number of records
  total: number = 0; // pagination total elements
  page: string; // nav page or search
  id: string; // id of the nav page
  searchTerm: string = ''; // search term from query string
  title: string = ''; // title of the page
  options: string[] = [];
  cards: PageCard[] = []; // cards to display on the page
  isLoading: boolean = true; // loading flag for initial content
  isDataFetched: boolean = false; // flag to display the pagination
  isLoad: boolean = false; // flag to show the loader between API calls
  inputFilters: any[] = [];
  selectedOption: string = ''; // For filter selection

  // Forms
  searchForm: FormGroup;
  filterForm: FormGroup;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private navService: NavService
  ) { }

  async ngOnInit() {
    // Initialize forms
    this.searchForm = new FormGroup({
      searchInput: new FormControl('')
    });

    // Default to "Contractor" customer type change it to get from local storage after pulling new dev branch after code push
    const customerType = "Contractor";

    // Load the home page data with query parameters
    await this.loadHomePage(customerType);

    this.isLoading = false;
  }

  async loadHomePage(queryParams: any) {
    this.isLoad = true; // Show the loader
    this.cards = [];

    // Set the query for the API call (this is hardcoded for now)
    const query = {
      "homeId": queryParams // Hardcoded for now, but you can get it from LocalStorage after Auth
    };

    // Fetch data using the service
    const res = await this.navService.getCardsByHomeParams(query);
    console.log("Response from API:", res);

    // Load the cards with the fetched data
    this.loadCards(res);

    this.isLoad = false; // Hide the loader
    this.isDataFetched = true; // Display pagination
  }

  loadCards(res: any) {
    this.cards = [];  // Reset cards array
    this.title = res.title || 'No Title'; // Set title
  
    console.log("Cards from response:", res.cards); // Log the cards from API
  
    // Check if 'cards' data exists in the response
    if (res.cards && res.cards.length > 0) {
      console.log("Processing cards...");
      
      for (let i = 0; i < res.cards.length; i++) {
        const result = res.cards[i];
  
        // Log each card to verify its structure
        console.log("Processing Card:", result);
  
        // Construct the card object
        const card = {
          id: result.id,
          type: result.type || 'unknown',  // Ensure 'type' is present in the response
          image: result.image || 'placeholder.png',  // Ensure there's an image, or use a placeholder
          title: result.title || 'No Title',  // Handle missing titles
          subtitle: result.subtitle || 'No subtitle', // Handle undefined subtitle
          link: result.link
        };
  
        console.log("Constructed Card:", card); // Log constructed card object
  
        this.cards.push(card); // Push to cards array
      }
  
      console.log("Final Cards Array:", this.cards); // Log the final cards array
    } else {
      console.log("No cards found in the response.");
    }
  
    // Handle filters if available
    if (res.filters) {
      this.filters = res.filters;
      console.log("Filters received:", res.filters); // Log filters
    } else {
      this.filters = []; // Ensure filters is an empty array if undefined
      console.log("No filters received from the API.");
    }
  
    // Pagination logic, handle undefined total
    this.total = res.total || this.cards.length; // Use cards length if total is undefined
    console.log("Total records:", this.total); // Log total records
  }
  

  // Search function for the search form
  searchProducts(event: Event) {
    event.preventDefault();
    const encodedSearchTerm = encodeURIComponent(this.searchTerm);
    this.router.navigate(['/search'], { queryParams: { searchTerm: encodedSearchTerm } });
  }

  // Pagination page change
  changePage(page: number): void {
    this.currentPage = page;
    // this.onSearch(); Uncomment when search is implemented
  }

  async onSearch() {
    if (this.isLoad) {
      return;  // Prevent multiple submissions
    }
    this.isLoad = true; // Showing the loader 
    this.cards = [];
    const searchTerm = this.searchForm.get('searchInput').value;
    const query = {
      limit: this.limit,
      page: this.currentPage,
      searchTerm: searchTerm
    };
   
    const res = await this.navService.getCardsByParams(query);
   
    this.total = res['total'];
    this.loadCards(res)
  }


}
