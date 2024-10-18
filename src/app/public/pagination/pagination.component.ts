import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-pagination',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './pagination.component.html',
  styleUrl: './pagination.component.scss'
})
export class PaginationComponent implements OnInit{
  @Input() currentPage: number = 1;
  @Input() total: number;
  @Input() limit: number;
  @Output() changePage = new EventEmitter<number>();

  pages: number[] = [];

  ngOnInit(): void {
    this.updatePages();
  }

  ngOnChanges(): void {
    this.updatePages(); // Update pages when inputs change
  }

  updatePages(): void {
    const pagesCount = Math.ceil(this.total / this.limit);
    this.pages = Array.from({ length: pagesCount }, (_, i) => i + 1);
  }

  onPageChange(page: number): void {
    this.changePage.emit(page);
  }
}
